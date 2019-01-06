from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException
from configparser import ConfigParser
import os
import time


class IvleDownloader:
    """
    An automatic IVLE files downloader using web scraping tool, Selenium

    Attributes
    ----------
    exec_path : str
        Path to chromedriver
    root_path : str
        Path to parent folder of the semester
    username : str
        Username
    password : str
        Password
    all_modules_files_urls : dict
        Dictionary with module code as key and url as value

    """

    def __init__(self, exec_path: str, root_path: str, username: str, password: str):
        self.exec_path = exec_path
        self.root_path = root_path
        self.user = username
        self.password = password
        self.all_modules_files_urls = {}

    @staticmethod
    def _find_all_modules_files_urls(driver: WebDriver):
        """
        Finds url to file section of each module

        Parameters
        ----------
        driver : Webdriver
            Driver with default download path

        Returns
        -------
        urls : dict
            Dictionary with module code as key and url as value

        """
        elements = driver.find_elements_by_css_selector('u')
        urls = {}
        for element in elements:
            try:
                module = element.find_element_by_tag_name('a').text
                url = str(element.find_element_by_tag_name('a').get_attribute('href'))
                # if module not opened yet
                if 'Default.aspx' not in url:
                    break
                url = url.replace('Module', 'File')
                urls[module] = url
            except NoSuchElementException:
                # only those non module element will have this exception
                pass
        return urls

    @staticmethod
    def _create_folders(path: str, new_folder: str):
        """
        Creates folder in given path if folder does not exist

        Parameters
        ----------
        path : str
            Path to create folder in
        new_folder : str
            Name of new folder

        """
        if new_folder not in os.listdir(path):
            print('Creating folder: {}'.format(new_folder))
            os.mkdir('{}/{}'.format(path, new_folder))

    def start(self):
        """
        Starts the download session

        """
        driver = self._get_driver()
        self.all_modules_files_urls = self._find_all_modules_files_urls(driver)
        self._download_all(driver)

    def _login(self, driver: WebDriver):
        """
        Logs user in

        Parameters
        ----------
        driver : WebDriver
            Driver with download path preference

        """
        driver.get('https://ivle.nus.edu.sg/')
        driver.find_element_by_id('ctl00_ctl00_ContentPlaceHolder1_userid').send_keys(self.user)
        driver.find_element_by_id('ctl00_ctl00_ContentPlaceHolder1_password').send_keys(self.password)
        driver.find_element_by_id('ctl00_ctl00_ContentPlaceHolder1_btnSignIn').click()

    def _get_driver(self, *args):
        """
        Gets a driver with given settings

        Parameters
        ----------
        *args
            If specific download path is provided in this optional argument,
            driver will be created with this preference. Else, a driver with
            default download path will be created.

        Returns
        -------
        driver : WebDriver
            Driver with default or specific preferences to download path

        """
        chrome_options = webdriver.ChromeOptions()
        if args:
            prefs = {'download.default_directory': args[0]}
            chrome_options.add_experimental_option('prefs', prefs)
            chrome_options.add_argument('--headless')
            driver = webdriver.Chrome(executable_path=self.exec_path, options=chrome_options)
        else:
            chrome_options.add_argument('--headless')
            driver = webdriver.Chrome(executable_path=self.exec_path, options=chrome_options)
        self._login(driver)
        return driver

    def _download_all(self, driver: WebDriver):
        """
        Downloads all files for all modules

        Parameters
        ----------
        driver : WebDriver
            Driver with download path preference

        """
        for module, url in self.all_modules_files_urls.items():
            module_path = '{}/{}'.format(self.root_path, module)
            if module not in os.listdir(self.root_path):
                os.mkdir(module_path)
            self._download_files_from_url(url, module_path, driver)

    def _download_files_from_url(self, url: str, path: str, driver: WebDriver):
        """
        Downloads all files from a given url into given path

        Parameters
        ----------
        url : str
            Url to download files from
        path : str
            Path to download files into
        driver : WebDriver
            Driver with download path preference

        """
        driver.get(url)
        table = driver.find_element_by_id('mainTable')
        # give buffer time to find element with id = 'mainTable'
        time.sleep(1)
        elements = table.find_elements_by_tag_name('a')
        missing_files = {}
        for element in elements:
            f_url = element.get_attribute('href')
            is_folder = 'default.aspx' in f_url
            if is_folder:
                f_path = '{}/{}'.format(path, element.text)
                self._create_folders(path, element.text)
                self._download_files_from_url(f_url, f_path, self._get_driver(f_path))
            else:
                # todo handle the case if prof updates a same file on a later date (check upload date vs download date)
                if element.text not in os.listdir(path):
                    missing_files[element.text] = f_url
        self._update_folder(missing_files, path, driver)
        driver.close()

    def _update_folder(self, files: dict, path: str, driver: WebDriver):
        """
        Downloads new files into given path

        Parameters
        ----------
        files : dict
            Dictionary with file name as key and download link as value
        path : str
            Path to download files into
        driver : WebDriver
            Driver with download path preference

        """
        for file_name, url in files.items():
            print('Downloading: {}'.format(file_name))
            driver.get(url)
            time.sleep(1)
            # is_malicious is true when chrome safebrowsing popup has appeared => no partial .crdownload file in path
            is_malicious = len(list(filter(lambda file: '.crdownload' in file, os.listdir(path)))) == 0
            if not is_malicious:
                # wait for file to download finish
                while file_name not in os.listdir(path):
                    time.sleep(1)
            else:
                print('{} is marked as dangerous by Chrome and will be skipped'.format(file_name))
                driver.close()
                driver = self._get_driver(path)


if __name__ == '__main__':
    config = ConfigParser()
    config.read('config.ini')

    EXEC_PATH = config['SETTINGS']['EXEC_PATH']
    ROOT_PATH = config['SETTINGS']['ROOT_PATH']
    USER = config['SETTINGS']['USERNAME']
    PASSWORD = config['SETTINGS']['PASSWORD']

    ivle_downloader = IvleDownloader(EXEC_PATH, ROOT_PATH, USER, PASSWORD)
    ivle_downloader.start()
