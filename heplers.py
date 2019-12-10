import webbrowser
import platform
import os

def open_chrome_browser()
    os_name = platform.system()
    if os_name == 'Windows':
        chrome_path = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe %s'
    elif os_name == 'Linux':
        chrome_path = r'/usr/bin/google-chrome %s'
    else:
        raise ValueError(f'unknown os: {os_name=}!')

    webbrowser.register('Chrome', None, webbrowser.BackgroundBrowser(chrome_path))
    link_path = os.path.join(os.getcwd(), 'index.html')
    webbrowser.get('Chrome').open_new_tab(link_path)
    
