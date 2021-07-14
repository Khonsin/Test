import os
import requests
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from lxml import etree
import time
from multiprocessing.dummy import Pool
import multiprocessing
import re
from numpy import repeat
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'
}
if not os.path.exists('./凤凰网'):
    os.mkdir('./凤凰网')
def connectChrome():
    options = Options()
    options.add_argument("--incognito")
    options.add_argument("--no-sandbox");
    options.add_argument("--disable-dev-shm-usage");
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_argument( "user-agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'")  # 进行UA伪装
    driver_path = os.getcwd() + "/chromedriver"
    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": """Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"""})
    driver.maximize_window()
    time.sleep(2)
    return driver
def scroll_to_bottom(driver):
    js = "return action=document.body.scrollHeight"  # 获取页面总高度
    last_height = 0
    new_height = driver.execute_script(js)
    while last_height < new_height:
        for i in range(last_height, new_height, 400):
            driver.execute_script('window.scrollTo(0,{})'.format(i))
            time.sleep(1)
        last_height = new_height
        new_height = driver.execute_script(js)
def crawl_detail_url(keyword):
    driver = connectChrome()
    detail_url_list = []
    driver.get('https://so.ifeng.com/?q='+keyword)
    time.sleep(2)
    video_button = driver.find_elements_by_xpath('//*[@id="root"]/div[2]/div[3]/div[1]/div/span[3]')[0]
    video_button.click()
    time.sleep(3)
    scroll_to_bottom(driver)
    original_page_source = driver.page_source
    original_tree = etree.HTML(original_page_source)
    li_list = original_tree.xpath('//*[@id="root"]/div[2]/div[3]/div[2]/ul/li')
    for li in li_list:
        detail_url = 'https:'+li.xpath('./a/@href')[0]
        detail_url_list.append(detail_url)
    driver.quit()
    return detail_url_list
def crawl_video_url(detail_url):
    detail_page_source = requests.get(url=detail_url, headers=headers).text
    video_url = re.findall( '"mobileUrl":"(.*?)","duration"', detail_page_source)[0]
    detail_tree = etree.HTML(detail_page_source)
    video_name = detail_tree.xpath('/html/head/title/text()')[0]
    video_data = {
        'video_name': video_name,
        'video_url': video_url
    }
    video_data_list.append(video_data)
def crawl_video(keyword, video_data):
    video_url = video_data['video_url']
    video_name = video_data['video_name']
    video_content = requests.get(url=video_url, headers=headers).content
    video_name = video_name.replace(' ', '').replace('\"', '')
    with open('./凤凰网/'+keyword+'/'+video_name+'.mp4', mode='wb') as fp:
        fp.write(video_content)
if __name__=='__main__':
    start_time = time.time()
    keyword_list = ['破甲弹', '火箭弹']
    for keyword in keyword_list:
        if not os.path.exists('./凤凰网/' + keyword):
            os.mkdir('./凤凰网/' + keyword)
        video_data_list = []
        detail_url_list = crawl_detail_url(keyword)
        print(len(detail_url_list))
        pool = Pool(multiprocessing.cpu_count())
        pool.map(crawl_video_url, detail_url_list)
        print(len(video_data_list))
        pool.starmap(crawl_video, zip(repeat(keyword, len(video_data_list)), video_data_list))
        pool.close()
        pool.join()
        video_data_list = []
    end_time = time.time()
    print('爬取总时长为：'+str(end_time-start_time))