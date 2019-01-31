from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException
from configparser import ConfigParser
import os
import time
import argparse


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
        driver : WebDriver
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
                # module not opened yet
                if 'Default.aspx' not in url:
                    break
                url = url.replace('Module', 'File')
                # module has two codes, pick first one
                if '/' in module:
                    module = module.split('/')[0]
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

    @staticmethod
    def _update_folder(files: dict, driver: WebDriver):
        """
        Downloads new files into given path

        Parameters
        ----------
        files : dict
            Dictionary with file name as key and download link as value
        driver : WebDriver
            Driver with download path preference

        """
        driver.get('chrome://downloads')
        for file_name, url in files.items():
            print('Downloading: {}'.format(file_name))
            driver.get(url)
            time.sleep(2)

            def get_download_status():
                pause_buttons = driver.find_elements_by_css_selector('body/deep/paper-button')
                if type(pause_buttons) == list:
                    return 'Pause' in list(map(lambda button: button.text, pause_buttons))
                else:
                    return 'Pause' == pause_buttons.text

            is_still_downloading = get_download_status()
            # todo - implement check with chrome://downloads for 'REMOVE FROM LIST' and 'KEEP DANGEROUS FILE'
            while is_still_downloading:
                time.sleep(2)
                is_still_downloading = get_download_status()

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
            download_path = args[0]
            prefs = {'download.default_directory': download_path}
            chrome_options.add_experimental_option('prefs', prefs)
        # unable to run headless for now
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--log-level=3')
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
            print('Entering {}...'.format(module))
            self._download_files_from_url(url, module_path, driver)
            driver = self._get_driver()

    def _download_modules(self, modules: list, driver: WebDriver):
        """
        Downloads all files for specific modules

        Parameters
        ----------
        modules : list
            List of specific modules to download
        driver : WebDriver
            Driver with download path preference

        """
        for module, url in self.all_modules_files_urls.items():
            if module not in modules:
                continue
            module_path = '{}/{}'.format(self.root_path, module)
            if module not in os.listdir(self.root_path):
                os.mkdir(module_path)
            print('Entering {}...'.format(module))
            self._download_files_from_url(url, module_path, driver)
            driver = self._get_driver()

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
            is_folder = 'default.aspx' in f_url and '#' not in f_url
            is_file = 'download.aspx' in f_url and '#' not in f_url
            if is_folder:
                print('Checking {} folder for updates...'.format(element.text))
                f_path = '{}/{}'.format(path, element.text)
                self._create_folders(path, element.text)
                self._download_files_from_url(f_url, f_path, self._get_driver(f_path))
            elif is_file:
                if element.text not in os.listdir(path):
                    missing_files[element.text] = f_url
        self._update_folder(missing_files, driver)
        driver.close()

    def start(self, *modules):
        """
        Starts the download session

        """
        driver = self._get_driver()
        self.all_modules_files_urls = self._find_all_modules_files_urls(driver)
        if modules:
            self._download_modules(modules[0], driver)
        else:
            self._download_all(driver)


if __name__ == '__main__':
    config = ConfigParser()
    config.read('config.ini')

    EXEC_PATH = config['SETTINGS']['EXEC_PATH']
    ROOT_PATH = config['SETTINGS']['ROOT_PATH']
    USER = config['SETTINGS']['USERNAME']
    PASSWORD = config['SETTINGS']['PASSWORD']

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--modules', nargs='*')
    args = parser.parse_args()

    ivle_downloader = IvleDownloader(EXEC_PATH, ROOT_PATH, USER, PASSWORD)
    ivle_downloader.start(args.modules)
