import gradio as gr
import os
import json
from datetime import datetime
from ai_processor import (
    analyze_submission,
    get_provider_display_name,
    get_provider_note,
)
from report_generator import generate_markdown_report, export_to_txt, export_to_word

title = "社区投稿智能助手 - 东莞社区志愿者工具"

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_config.json")

PROVIDER_CHOICES = [
    ("DeepSeek (推荐, 免费)", "deepseek"),
    ("通义千问 (阿里云, 免费额度)", "dashscope"),
    ("智谱GLM (免费额度)", "zhipu"),
    ("Kimi (月之暗面, 免费额度)", "kimi"),
]


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(provider, api_key):
    try:
        config = {"provider": provider, "api_key": api_key}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def clear_config():
    try:
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        return True
    except Exception:
        return False


saved_config = load_config()
default_provider = saved_config.get("provider", "deepseek")
default_api_key = saved_config.get("api_key", "")


def on_provider_change(provider_id):
    display_name = get_provider_display_name(provider_id)
    note = get_provider_note(provider_id)

    guide = f"**免费额度**：{note}"

    if provider_id == "deepseek":
        guide += " | 访问 DeepSeek 官网注册 -> API Keys 页面创建 -> 复制密钥"
    elif provider_id == "dashscope":
        guide += " | 访问阿里云 DashScope 注册 -> API Key 管理创建 -> 复制密钥"
    elif provider_id == "zhipu":
        guide += " | 访问智谱AI开放平台注册 -> API 密钥页面创建 -> 复制密钥"
    elif provider_id == "kimi":
        guide += " | 访问 Moonshot AI 注册 -> API 密钥页面创建 -> 复制密钥"
        guide += " | 访问 Moonshot AI 注册 -> API 密钥页面创建 -> 复制密钥"

    return gr.update(label=f"{display_name} API 密钥", placeholder=f"输入 {display_name} API 密钥..."), guide


def save_config_action(provider_id, api_key_input):
    key = api_key_input.strip() if api_key_input else ""
    if not key:
        return "请先输入API密钥再保存"
    if save_config(provider_id, key):
        return f"配置已保存 (提供商: {get_provider_display_name(provider_id)})"
    return "保存失败，请检查权限"


def clear_config_action():
    if clear_config():
        config_state = {"provider": "deepseek", "api_key": ""}
        return config_state, gr.update(value="deepseek"), gr.update(value=""), "配置已清除，请重新输入"
    return {"provider": "deepseek", "api_key": ""}, gr.update(value="deepseek"), gr.update(value=""), "清除失败"


def process_url_submission(url, provider_id, api_key_input):
    if not url or not url.strip():
        return None, "请输入链接地址！", None

    resolved_key = api_key_input.strip() if api_key_input and api_key_input.strip() else None

    try:
        result = analyze_submission(url, provider=provider_id, api_key=resolved_key, is_url=True)
        report = generate_markdown_report(result, f"[链接] {url}")
        return report, "分析完成", report

    except Exception as e:
        error_msg = str(e)
        if "API" in error_msg or "密钥" in error_msg:
            return None, f"配置错误：{error_msg}", None
        return None, f"分析失败：{error_msg}", None


def process_submission(text, provider_id, api_key_input):
    if not text or not text.strip():
        return None, "请输入投稿内容！", None

    resolved_key = api_key_input.strip() if api_key_input and api_key_input.strip() else None

    try:
        result = analyze_submission(text, provider=provider_id, api_key=resolved_key)
        report = generate_markdown_report(result, text)
        return report, "分析完成", report

    except Exception as e:
        error_msg = str(e)
        if "API" in error_msg or "密钥" in error_msg:
            return None, f"配置错误：{error_msg}", None
        return None, f"分析失败：{error_msg}", None


def export_txt(report_text):
    if not report_text:
        return None, "请先进行分析再导出"
    try:
        filepath = export_to_txt(report_text)
        filename = os.path.basename(filepath)
        return filepath, f"TXT 导出成功：{filename}"
    except Exception as e:
        return None, f"导出失败：{str(e)}"


def export_word(report_text):
    if not report_text:
        return None, "请先进行分析再导出"
    try:
        filepath = export_to_word(report_text)
        filename = os.path.basename(filepath)
        return filepath, f"Word 导出成功：{filename}"
    except Exception as e:
        return None, f"导出失败：{str(e)}"


with gr.Blocks(title=title) as app:
    report_state = gr.State(None)
    config_state = gr.State({"provider": default_provider, "api_key": default_api_key})

    gr.HTML(
        f"""
        <div style="text-align:center; margin-bottom:1.5rem; padding:1rem 0;">
            <h1 style="font-size:2rem; font-weight:700; background:linear-gradient(135deg,#1a5276,#2e86c1);
                -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
                display:inline-flex; align-items:center; gap:12px; margin:0;">
                社区投稿智能助手
            </h1>
            <div style="color:#5d6d7e; margin-top:8px; font-size:1rem;">
                东莞社区志愿者工具  |  AI赋能 高效处理投稿
            </div>
        </div>
        """
    )

    with gr.Row(equal_height=False):
        with gr.Column(scale=4, min_width=300):
            with gr.Group():
                gr.Markdown("### AI模型与密钥配置")
                provider_dropdown = gr.Dropdown(
                    choices=PROVIDER_CHOICES,
                    value=default_provider,
                    label="选择AI模型",
                    interactive=True,
                )
                api_key_hint = gr.Markdown(
                    "免费额度：注册送500万tokens | 访问官网注册 -> API Keys 页面创建 -> 复制密钥"
                )
                api_key_input = gr.Textbox(
                    label="API 密钥",
                    placeholder="输入 sk- 开头的 API Key...",
                    type="password",
                    lines=1,
                    value=default_api_key,
                )
                with gr.Row():
                    save_config_btn = gr.Button("保存配置", variant="secondary", scale=1)
                    clear_config_btn = gr.Button("清除配置", variant="secondary", scale=1)
                config_status = gr.Textbox(label="", lines=1, interactive=False)

            with gr.Group():
                gr.Markdown(
                    "### 投稿内容",
                )
                with gr.Tabs():
                    with gr.TabItem("粘贴文本"):
                        text_input = gr.Textbox(
                            label="粘贴事件描述（支持微信/小红书/抖音内容）",
                            placeholder="例如：今天在XX小区发现垃圾堆积严重，许多居民抱怨影响到生活，物业一直未处理，大家情绪激动...",
                            lines=8,
                            max_lines=20,
                        )
                        text_analyze_btn = gr.Button("分析文本内容", variant="primary", size="lg")
                    with gr.TabItem("从链接获取"):
                        url_input = gr.Textbox(
                            label="输入文章链接",
                            placeholder="https://...",
                            lines=3,
                        )
                        url_analyze_btn = gr.Button("分析链接内容", variant="primary", size="lg")

            with gr.Accordion("试试示例投稿", open=False):
                gr.Examples(
                    examples=[
                        ["我们学校食堂最近涨价了，以前一荤一素8块钱，现在要12块钱。学生每个月生活费本来就有限，很多同学都反映吃不起了。而且食堂阿姨打菜的手越来越抖，肉都给得很少。希望学校能管管。"],
                        ["小区门口的路灯坏了快一个月了，晚上出门一片漆黑。跟物业反映了好几次都没人管。昨天晚上有个老人家差点摔倒。这条路还是很多学生上下学的必经之路，太危险了。"],
                        ["工业园区那家化工厂又在半夜偷偷排放废气了，浓烟滚滚的，味道特别刺鼻。附近几个小区的居民都不敢开窗户。我们打12345投诉了好几次，每次都说在处理，但问题一直没解决。"],
                    ],
                    inputs=text_input,
                    label="",
                    examples_per_page=3,
                )

        with gr.Column(scale=6, min_width=360):
            with gr.Group():
                gr.Markdown("### 分析报告")
                report_display = gr.Textbox(
                    label="",
                    lines=20,
                    max_lines=40,
                    interactive=False,
                    value="点击「分析文本内容」或「分析链接内容」按钮，生成分析报告",
                )
                status_output = gr.Markdown("填写投稿内容，选择AI模型，然后点击分析按钮")
                with gr.Row():
                    export_txt_btn = gr.Button("导出 TXT", variant="secondary", scale=1)
                    export_word_btn = gr.Button("导出 Word", variant="secondary", scale=1)
                export_status = gr.Textbox(label="", lines=1, interactive=False)

    gr.Markdown(
        "社区志愿者智能工具 - 调用 AI API 实现分类/摘要/热度评分 | 数据仅用于辅助决策"
    )

    provider_dropdown.change(
        fn=on_provider_change,
        inputs=[provider_dropdown],
        outputs=[api_key_input, api_key_hint],
    )

    save_config_btn.click(
        fn=save_config_action,
        inputs=[provider_dropdown, api_key_input],
        outputs=[config_status],
    )

    clear_config_btn.click(
        fn=clear_config_action,
        inputs=[],
        outputs=[config_state, provider_dropdown, api_key_input, config_status],
    )

    text_analyze_btn.click(
        fn=process_submission,
        inputs=[text_input, provider_dropdown, api_key_input],
        outputs=[report_state, status_output, report_display],
    )

    url_analyze_btn.click(
        fn=process_url_submission,
        inputs=[url_input, provider_dropdown, api_key_input],
        outputs=[report_state, status_output, report_display],
    )

    export_txt_btn.click(
        fn=export_txt,
        inputs=[report_state],
        outputs=[gr.File(None), export_status],
    )

    export_word_btn.click(
        fn=export_word,
        inputs=[report_state],
        outputs=[gr.File(None), export_status],
    )


if __name__ == "__main__":
    app.launch(server_name="127.0.0.1", server_port=7861, share=False, theme=gr.themes.Soft())
