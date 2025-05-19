#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import asyncio
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError
from tqdm import tqdm
import re
import argparse
from urllib.parse import urlparse

# 用户账号和密码 (如果需要登录)
USERNAME = "your_email@example.com"
PASSWORD = "your_password"

async def is_login_page(page):
    """检测当前页面是否为登录页面"""
    try:
        # 检查URL是否包含登录相关字符串
        current_url = page.url
        if "login" in current_url.lower() or "sign-in" in current_url.lower():
            return True
        
        # 检查页面是否包含登录表单元素
        password_field = await page.query_selector("input[type='password']")
        login_button = await page.query_selector("button:has-text('登录'), button:has-text('Login'), button:has-text('Sign in')")
        
        if password_field and login_button:
            return True
        
        # 检查页面内容是否包含登录相关文本
        content = await page.content()
        login_terms = ["登录", "login", "sign in", "signin"]
        if any(term in content.lower() for term in login_terms):
            return True
            
        return False
    except Exception as e:
        print(f"检查登录页面时出错: {e}")
        return False

async def login(page):
    """在当前页面尝试登录"""
    try:
        print("\n检测到登录页面，尝试登录...")
        
        # 查找并填写邮箱输入框
        email_selectors = [
            "input[type='email']", 
            "input[name='email']",
            "input[placeholder*='邮箱']",
            "input[placeholder*='email']",
            "input[id*='email']",
            "input.email"
        ]
        
        # 尝试使用不同的选择器查找邮箱输入框
        email_input = None
        for selector in email_selectors:
            email_input = await page.query_selector(selector)
            if email_input:
                break
        
        # 如果没找到，尝试使用XPath
        if not email_input:
            email_input = await page.query_selector("//input[@type='email' or @type='text']")
        
        if email_input:
            await email_input.fill(USERNAME)
            print("已输入用户名")
        else:
            # 使用JavaScript注入
            await page.evaluate(f"""
                var inputs = document.getElementsByTagName('input');
                for(var i = 0; i < inputs.length; i++) {{
                    if(inputs[i].type.toLowerCase() === 'email' || 
                       inputs[i].type.toLowerCase() === 'text' || 
                       inputs[i].name.toLowerCase().includes('email') || 
                       inputs[i].placeholder.toLowerCase().includes('email')) {{
                        inputs[i].value = "{USERNAME}";
                    }}
                }}
            """)
            print("已通过JavaScript输入用户名")
        
        # 查找并填写密码输入框
        password_selectors = [
            "input[type='password']",
            "input[name='password']",
            "input[placeholder*='密码']",
            "input[placeholder*='password']",
            "input[id*='password']"
        ]
        
        # 尝试使用不同的选择器查找密码输入框
        password_input = None
        for selector in password_selectors:
            password_input = await page.query_selector(selector)
            if password_input:
                break
        
        if password_input:
            await password_input.fill(PASSWORD)
            print("已输入密码")
        else:
            # 使用JavaScript注入
            await page.evaluate(f"""
                var inputs = document.getElementsByTagName('input');
                for(var i = 0; i < inputs.length; i++) {{
                    if(inputs[i].type.toLowerCase() === 'password') {{
                        inputs[i].value = "{PASSWORD}";
                    }}
                }}
            """)
            print("已通过JavaScript输入密码")
        
        # 查找并点击登录按钮
        login_button_selectors = [
            "button[type='submit']",
            "button.login-btn",
            "button.submit-btn",
            "input[type='submit']",
            "button.btn-primary",
            "button:has-text('登录')",
            "button:has-text('Login')",
            "button:has-text('Sign in')"
        ]
        
        # 尝试使用不同的选择器查找登录按钮
        login_button = None
        for selector in login_button_selectors:
            login_button = await page.query_selector(selector)
            if login_button:
                break
        
        if login_button:
            await login_button.click()
            print("已点击登录按钮")
        else:
            # 尝试提交表单
            if password_input:
                await password_input.press("Enter")
                print("已提交表单")
            else:
                print("无法找到登录按钮，请手动登录")
        
        # 等待登录完成
        await page.wait_for_timeout(5000)  # 等待5秒
        
        # 检查是否登录成功
        if await is_login_page(page):
            print("自动登录可能失败")
            return False
        else:
            print("登录成功!")
            return True
    except Exception as e:
        print(f"登录过程出错: {e}")
        return False

async def close_popups(page):
    """关闭页面上的弹窗和提示"""
    try:
        # 1. 首先尝试点击右上角的叉叉按钮(通常是关闭弹窗的最常见方式)
        close_x_selectors = [
            "button.close", 
            ".close",
            ".modal-close",
            "button[aria-label='Close']",
            ".dialog-close-button",
            "[data-testid='close-button']",
            ".modal .close",
            ".dialog .close",
            ".popup .close",
            "button.modal-close",
            "button.dialog-close",
            "button.popup-close"
        ]
        
        # 查找可能的关闭按钮
        for selector in close_x_selectors:
            try:
                close_buttons = await page.query_selector_all(selector)
                for button in close_buttons:
                    # 检查按钮是否可见
                    if await button.is_visible():
                        # 点击前等待确保元素稳定
                        await button.hover()  # 先悬停在按钮上
                        await page.wait_for_timeout(300)
                        await button.click()
                        print(f"已点击关闭按钮: {selector}")
                        await page.wait_for_timeout(1000)
                        return True
            except Exception as e:
                # print(f"尝试点击 {selector} 时出错: {e}") # 调试时可以取消注释
                continue

        # 2. 针对性查找包含 × 符号的元素
        close_x_symbols = [
            "text='×'",
            "text='✕'",
            "text='✖'",
            "text='X'",
            "[aria-label='Close'] >> text=×",
            "[title='Close'] >> text=×"
        ]
        
        for selector in close_x_symbols:
            try:
                x_button = await page.query_selector(selector)
                if x_button and await x_button.is_visible():
                    await x_button.hover()
                    await page.wait_for_timeout(300)
                    await x_button.click()
                    print(f"已点击包含 × 符号的按钮: {selector}")
                    await page.wait_for_timeout(1000)
                    return True
            except Exception:
                continue

        # 3. 尝试通过XPath查找右上角位置的关闭按钮
        try:
            # 查找位于弹窗右上角的按钮
            corner_buttons = await page.query_selector_all("xpath=//div[contains(@class, 'modal') or contains(@class, 'dialog') or contains(@class, 'popup')]//button[position()=1]")
            for button in corner_buttons:
                if await button.is_visible():
                    await button.hover()
                    await page.wait_for_timeout(300)
                    await button.click()
                    print("已点击弹窗右上角按钮")
                    await page.wait_for_timeout(1000)
                    return True
        except Exception:
            pass

        # 4. 查找Next和Previous按钮
        try:
            # 查找Next/Previous按钮 - 为顺序浏览弹窗支持
            next_button = await page.query_selector("button:has-text('Next')")
            if next_button and await next_button.is_visible():
                await next_button.click()
                print("已点击'Next'按钮")
                await page.wait_for_timeout(1000)
                # 继续检查是否还有其他弹窗
                await close_popups(page)
                return True
            
            # 如果没有Next按钮，但找到了关闭按钮
            done_button = await page.query_selector("button:has-text('Done'), button:has-text('Finish'), button:has-text('Got it')")
            if done_button and await done_button.is_visible():
                await done_button.click()
                print("已点击'Done/Finish/Got it'按钮")
                await page.wait_for_timeout(1000)
                return True
        except Exception:
            pass

        # 5. 尝试点击任何可能含有关闭意图的按钮
        try:
            close_text_buttons = await page.query_selector_all("button, a")
            for button in close_text_buttons:
                if await button.is_visible():
                    button_text = await button.text_content()
                    if button_text:
                        button_text = button_text.lower().strip()
                        if any(keyword in button_text for keyword in ["close", "got it", "ok", "next", "dismiss", "关闭", "确定", "知道了"]):
                            await button.hover()
                            await page.wait_for_timeout(300)
                            await button.click()
                            print(f"已点击文本为'{button_text}'的按钮")
                            await page.wait_for_timeout(1000)
                            return True
        except Exception:
            pass
        
        # 6. 通用的JavaScript方法尝试关闭各类弹窗
        try:
            # 使用JavaScript查找并点击可能的关闭按钮
            # 重新编写JS代码，使用标准的三引号语法
            close_button_clicked = await page.evaluate("""
                () => { 
                    function closePopupsInternal() {
                        var closeSymbols = ['×', '✕', '✖', 'X', 'x'];
                        var elements = document.querySelectorAll('*');
                        
                        for (var i = 0; i < elements.length; i++) {
                            var el = elements[i];
                            var text = el.textContent ? el.textContent.trim() : '';
                            
                            if (closeSymbols.includes(text) && el.offsetParent !== null) {
                                el.click();
                                console.log('JS: 点击了关闭符号按钮');
                                return true;
                            }
                            
                            if (el.tagName === 'BUTTON' || el.tagName === 'A') {
                                var className = el.className ? el.className.toLowerCase() : '';
                                var ariaLabel = el.getAttribute('aria-label');
                                if ((className.includes('close') || 
                                    className.includes('dismiss') || 
                                    (ariaLabel && ariaLabel.toLowerCase() === 'close')) && 
                                    el.offsetParent !== null) {
                                    el.click();
                                    console.log('JS: 点击了带有关闭类名/aria-label的按钮');
                                    return true;
                                }
                            }
                        }
                        
                        var actionButtons = document.querySelectorAll('button');
                        for (var i = 0; i < actionButtons.length; i++) {
                            var button = actionButtons[i];
                            var text = button.textContent ? button.textContent.toLowerCase().trim() : '';
                            if ((text === 'next' || text === 'done' || text === 'finish' || text === 'got it' || text === 'accept' || text === 'allow') && 
                                button.offsetParent !== null) {
                                button.click();
                                console.log('JS: 点击了操作按钮: ' + text);
                                return true;
                            }
                        }
                        
                        var dialogs = document.querySelectorAll('.modal, .dialog, .popup, [role="dialog"]');
                        for (var i = 0; i < dialogs.length; i++) {
                            var dialog = dialogs[i];
                            var buttonsInDialog = dialog.querySelectorAll('button');
                            if (buttonsInDialog.length > 0) {
                                if (buttonsInDialog[0].offsetParent !== null) {
                                    buttonsInDialog[0].click();
                                    console.log('JS: 点击了对话框的第一个按钮');
                                    return true;
                                }
                                if (buttonsInDialog.length > 1 && buttonsInDialog[buttonsInDialog.length-1].offsetParent !== null) {
                                    buttonsInDialog[buttonsInDialog.length-1].click();
                                    console.log('JS: 点击了对话框的最后一个按钮');
                                    return true;
                                }
                            }
                        }
                        return false;
                    }
                    return closePopupsInternal();
                }
            """)
            
            if close_button_clicked:
                print("已通过JavaScript点击关闭按钮")
                await page.wait_for_timeout(1000)
                return True
        except Exception as e:
            print(f"JavaScript关闭弹窗失败: {e}") # 保持此日志以观察是否修复
        
        # 检查是否有弹窗仍然存在
        modals = await page.query_selector_all(".modal, .dialog, .popup, [role='dialog']")
        if not modals: # 如果modals列表为空，直接返回False
            print("未发现需要关闭的弹窗 (通过选择器)")
            return False

        visible_modals = [modal for modal in modals if await modal.is_visible()]
        
        if not visible_modals:
            print("未发现可见的弹窗")
            return False
        else:
            print(f"检测到 {len(visible_modals)} 个弹窗，但无法自动关闭")
            return False # 明确返回False
            
    except Exception as e:
        print(f"尝试关闭弹窗时出错: {e}")
        return False

async def take_screenshot(url, output_path, timeout=90000):
    """使用增强的Playwright方法访问URL并截图，解决网站反爬检测问题"""
    browser = None
    try:
        async with async_playwright() as p:
            print(f"使用增强截图方式访问: {url}")
            
            # 使用启动参数来隐藏自动化特征
            browser_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-features=site-per-process',
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            ]
            
            # 使用有头模式以获得更好的渲染效果
            browser = await p.chromium.launch(
                headless=False,
                args=browser_args
            )
            
            # 使用特殊的上下文配置
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},  # 标准屏幕尺寸
                java_script_enabled=True,
                ignore_https_errors=True,
                device_scale_factor=1.0,
                has_touch=False,
                is_mobile=False,
                locale="en-US"
            )
            
            # 先创建页面
            page = await context.new_page()
            
            # 使用CDP隐藏自动化特征
            cdp_session = await context.new_cdp_session(page)
            await cdp_session.send('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // 隐藏其他常见的自动化指标
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({state: Notification.permission}) :
                        originalQuery(parameters)
                );
                
                // 添加/修改一些常规只读属性，使其难以检测
                Object.defineProperties(navigator, {
                    plugins: { get: () => [1, 2, 3, 4, 5] },
                    languages: { get: () => ['en-US', 'en'] }
                });
                '''
            })
            
            # 设置超时
            page.set_default_navigation_timeout(timeout)
            page.set_default_timeout(timeout)

            print(f"导航到URL: {url}")
            # 使用更接近人类行为的导航方式
            await page.goto(url, wait_until='networkidle', timeout=timeout)
            
            print("应用增强截图处理方式...")
            # 禁用CSS动画和过渡效果
            await page.add_style_tag(content="""
                * {
                    transition: none !important;
                    animation: none !important;
                    transform: none !important;
                }
            """)
            
            # 等待页面元素稳定
            await page.wait_for_timeout(5000)
            
            # 检查是否需要登录
            if await is_login_page(page):
                login_successful = await login(page)
                if not login_successful:
                    print(f"登录失败 ({url})")
                    return False
                print(f"重新访问URL: {url}")
                await page.goto(url, wait_until='networkidle', timeout=timeout)
                await page.wait_for_timeout(5000)
                if await is_login_page(page):
                    print(f"登录后仍是登录页 ({url})")
                    return False
            
            # 模拟正常用户行为：随机鼠标移动和滚动
            print("模拟用户行为...")
            for _ in range(3):  # 鼠标移动次数
                x = 100 + (1820 * 0.7)  # 在页面上部区域移动
                y = 100 + (800 * 0.6)  # 保持在上半部分
                await page.mouse.move(x, y)
                await page.wait_for_timeout(500)  # 短暂停顿
            
            # 缓慢滚动以更自然地加载页面
            print("缓慢滚动页面...")
            
            # 先快速预览整个页面
            for scroll_pos in [300, 600, 1000, 1500, 0]:  # 多个滚动位置，最后回到顶部
                await page.evaluate(f'window.scrollTo(0, {scroll_pos});')
                await page.wait_for_timeout(800)
            
            # 然后更慢地从顶部滚到底部，给足时间加载内容
            scroll_height = await page.evaluate('document.body.scrollHeight;')
            view_height = await page.evaluate('window.innerHeight;')
            scroll_steps = min(10, max(5, int(scroll_height / view_height)))
            step_size = scroll_height / scroll_steps
            
            print(f"分{scroll_steps}步滚动页面，总高度: {scroll_height}px...")
            for i in range(scroll_steps + 1):
                current_pos = i * step_size
                await page.evaluate(f'window.scrollTo(0, {current_pos});')
                
                # 每次滚动后稍等一会，让更多内容加载
                await page.wait_for_timeout(1000)
                
                # 尝试点击某些可能的交互元素（如Cookie通知）
                await close_popups(page)
            
            # 回到顶部，从新开始观察页面加载
            await page.evaluate('window.scrollTo(0, 0);')
            await page.wait_for_timeout(3000)
            
            # 等待关键内容显示
            try:
                # 等待页面主标题或主要内容元素出现
                await page.wait_for_selector('h1, .main-title, .hero-title, [class*="title"], [class*="heading"]', 
                                           timeout=10000, state='visible')
                print("找到页面标题元素")
                
                # 尝试获取更多可能的关键内容
                await page.wait_for_selector('p, .description, article, [class*="content"]', 
                                           timeout=8000, state='visible')
                print("找到页面内容元素")
            except Exception as e:
                print(f"等待内容元素时出错: {e}")
            
            # 确保所有图片加载完成
            print("确保所有图片加载完成...")
            await page.evaluate("""
                async () => {
                    const images = Array.from(document.images);
                    const promises = [];
                    for (const img of images) {
                        if (!img.complete || img.naturalWidth === 0) {
                            promises.push(new Promise((resolve, reject) => {
                                img.onload = () => { console.log('Image loaded:', img.src); resolve(); };
                                img.onerror = () => { console.log('Image error:', img.src); resolve(); };
                                if (!img.src) resolve();
                            }));
                        }
                    }
                    await Promise.race([
                        Promise.all(promises),
                        new Promise(resolve => setTimeout(resolve, 10000))
                    ]);
                }
            """)
            
            # 最后，给页面最终的等待时间，让页面完全稳定
            print("最终等待，确保页面完全加载...")
            await page.wait_for_timeout(8000)  # 等待8秒
            
            # 再次回到顶部
            await page.evaluate('window.scrollTo(0, 0);')
            await page.wait_for_timeout(2000)
            
            # 直接截全屏
            print(f"开始截图，URL: {url}")
            await page.screenshot(path=output_path, full_page=True, timeout=60000)
            print(f"截图成功保存至: {output_path}")
            return True
    except TimeoutError as te:
        print(f"截图时发生超时错误 ({url}): {te}")
        return False
    except Exception as e:
        print(f"截图时发生一般错误 ({url}): {e}")
        import traceback
        print(traceback.format_exc())
        return False
    finally:
        if browser:
            await browser.close()
            print(f"浏览器已关闭 ({url})")

def get_clean_folder_name(text):
    """将文本转换为有效的文件夹名称"""
    if not text or pd.isna(text):
        return "未分类"
    
    # 截取前30个字符，避免文件夹名过长
    text = str(text)[:30]
    
    # 移除非法字符
    text = re.sub(r'[\\/*?:"<>|]', "", text)
    text = text.strip()
    
    # 如果为空，返回默认名称
    if not text:
        return "未分类"
    
    return text

async def process_csv(csv_path, output_dir):
    """处理CSV文件并下载截图"""
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取CSV文件
    try:
        df = pd.read_csv(csv_path)
        print(f"成功读取CSV文件，共 {len(df)} 行数据")
        print(f"CSV 文件列名: {', '.join(df.columns)}")
    except Exception as e:
        print(f"读取CSV文件时发生错误: {e}")
        return
    
    # 检查必要的列是否存在
    if 'prod_url' not in df.columns:
        print("CSV文件中缺少'prod_url'列")
        return
    
    # 确保case_name列存在
    if 'case_name' not in df.columns:
        print("警告: CSV文件中没有'case_name'列，所有截图将保存在同一文件夹中")
        df['case_name'] = "未分类"
    
    # 按case_name分组
    for case_name, group_df in df.groupby('case_name'):
        clean_case_name = get_clean_folder_name(case_name)
        group_dir = os.path.join(output_dir, clean_case_name)
        os.makedirs(group_dir, exist_ok=True)
        
        print(f"\n处理查询组: {clean_case_name} (共 {len(group_df)} 个URL)")
        
        # 统计已存在和需要处理的URL数量
        existing_files = 0
        urls_to_process = 0
        
        # 遍历该组中的每个URL并截图
        for i, (_, row) in enumerate(tqdm(group_df.iterrows(), desc=f"组 {clean_case_name} 的截图", total=len(group_df))):
            url = row.get('prod_url')
            if pd.isna(url) or not url:
                continue
                
            # 创建包含site_type的文件名
            site_type = row.get('site_type', "Unknown")
            filename = f"{site_type.lower()}.png"
            
            output_path = os.path.join(group_dir, filename)
            
            # 检查文件是否已存在
            if os.path.exists(output_path):
                print(f"\n文件已存在，跳过: {output_path}")
                existing_files += 1
                continue
            
            urls_to_process += 1
            
            # 尝试获取截图
            print(f"\n正在处理 {url} ({site_type})")
            success = await take_screenshot(url, output_path)
            
            if success:
                print(f"截图已保存到: {output_path}")
            else:
                print(f"无法截取 {url} 的截图")
        
        print(f"\n组 {clean_case_name} 处理完成: {existing_files} 个文件已存在，{urls_to_process} 个URL已处理")

async def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="增强版网页截图工具，支持从CSV批量截图或单个URL截图。")
    parser.add_argument("--url", type=str, help="需要单独截图的URL。")
    parser.add_argument("--output", type=str, help="单个URL截图的输出文件名（可选，可包含路径）。")
    parser.add_argument("--csv", type=str, default="case_urls.csv", help="CSV文件路径（可选，默认为case_urls.csv）")
    parser.add_argument("--outdir", type=str, default="enhanced_screenshots", help="输出目录名（可选，默认为enhanced_screenshots）")
    
    args = parser.parse_args()

    if args.url:
        # 单个URL截图模式
        single_url = args.url
        output_file_path = args.output
        
        if not output_file_path:
            # 如果未指定输出路径，创建默认路径和文件名
            domain = urlparse(single_url).netloc.replace(".", "_")
            # 移除非法字符并截断
            safe_domain = re.sub(r'[\\/*?:"<>|]', '', domain)[:50]
            filename = f"enhanced_{safe_domain}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
            output_dir_single = "enhanced_single"
            os.makedirs(output_dir_single, exist_ok=True)
            output_file_path = os.path.join(output_dir_single, filename)
        else:
            # 如果指定了输出路径，确保目录存在
            output_dir_single = os.path.dirname(output_file_path)
            if output_dir_single:
                 os.makedirs(output_dir_single, exist_ok=True)

        print(f"开始为单个URL截图: {single_url}")
        print(f"截图将保存至: {output_file_path}")
        
        success = await take_screenshot(single_url, output_file_path)
        if success:
            print(f"单个URL截图成功: {output_file_path}")
        else:
            print(f"单个URL截图失败: {single_url}")
        return

    # 批量CSV处理模式
    csv_path = args.csv
    output_dir = args.outdir 
    
    # 预检查任务状态
    print("预检查任务状态...")
    try:
        df = pd.read_csv(csv_path)
        total_urls = len(df)
        completed_urls = 0
        pending_urls = 0
        
        # 确保case_name列存在
        if 'case_name' not in df.columns:
            df['case_name'] = "未分类"
        
        # 按case_name分组检查
        for case_name, group_df in df.groupby('case_name'):
            clean_case_name = get_clean_folder_name(case_name)
            group_dir = os.path.join(output_dir, clean_case_name)
            
            # 确保目录存在
            os.makedirs(group_dir, exist_ok=True)
            
            group_completed = 0
            group_pending = 0
            
            # 检查每个URL对应的截图是否已存在
            for _, row in group_df.iterrows():
                url = row.get('prod_url')
                if pd.isna(url) or not url:
                    continue
                    
                site_type = row.get('site_type', "Unknown")
                filename = f"{site_type.lower()}.png"
                output_path = os.path.join(group_dir, filename)
                
                if os.path.exists(output_path):
                    group_completed += 1
                    completed_urls += 1
                else:
                    group_pending += 1
                    pending_urls += 1
            
            print(f"组 {clean_case_name}: {group_completed}/{len(group_df)} 已完成, {group_pending} 待处理")
        
        print(f"\n总任务状态: {completed_urls}/{total_urls} 已完成 ({completed_urls/total_urls*100:.1f}%), {pending_urls} 待处理")
        
        if pending_urls == 0:
            print("所有截图任务已完成！无需继续执行。")
            return
        
        print("\n开始处理待完成的截图任务...\n")
    except Exception as e:
        print(f"预检查任务状态时出错: {e}")
    
    # 处理CSV
    await process_csv(csv_path, output_dir)
    
    print("增强截图下载完成！")

if __name__ == "__main__":
    # 运行主异步函数
    asyncio.run(main()) 