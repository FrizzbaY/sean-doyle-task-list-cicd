import os
import uuid

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = os.environ.get("APP_ADDRESS", "http://127.0.0.1:8000")
WAIT_SECONDS = 10


def row_path(title):
    return f"//li[span[@class='task-title' and text()='{title}']]"   # the list item holding this title


def completed_row_path(title):
    return f"//li[contains(@class, 'completed')][span[@class='task-title' and text()='{title}']]"


@pytest.fixture
def browser():
    options = webdriver.ChromeOptions()
    if os.environ.get("BROWSER_HEADLESS") == "1":   # the pipeline sets this, so no window opens
        options.add_argument("--headless")
        options.add_argument("--window-size=1280,900")
    driver = webdriver.Chrome(options=options)
    driver.get(BASE_URL)
    yield driver
    driver.quit()


@pytest.fixture
def title(browser):
    name = f"browser test {uuid.uuid4().hex[:8]}"   # unique, so tests never match each other's tasks
    yield name
    browser.get(BASE_URL)
    for button in browser.find_elements(By.XPATH, row_path(name) + "//button[@class='delete-task']"):
        button.click()   # removes the task if the test left it behind
        wait_until(browser, EC.invisibility_of_element_located((By.XPATH, row_path(name))))   # so the browser is not closed mid-request


def wait_until(browser, condition):
    WebDriverWait(browser, WAIT_SECONDS).until(condition)


def add_task(browser, title):
    browser.find_element(By.ID, "task-title").send_keys(title)
    browser.find_element(By.ID, "add-task").click()
    wait_until(browser, EC.presence_of_element_located((By.XPATH, row_path(title))))


def test_add_task_appears_in_list(browser, title):
    add_task(browser, title)
    row = browser.find_element(By.XPATH, row_path(title))
    assert "completed" not in row.get_attribute("class")


def test_complete_task_marks_it_completed(browser, title):
    add_task(browser, title)
    browser.find_element(By.XPATH, row_path(title) + "//button[@class='complete-task']").click()
    wait_until(browser, EC.presence_of_element_located((By.XPATH, completed_row_path(title))))
    row = browser.find_element(By.XPATH, completed_row_path(title))
    assert not row.find_elements(By.CSS_SELECTOR, ".complete-task")   # the Complete button is gone


def test_delete_task_removes_it_from_list(browser, title):
    add_task(browser, title)
    browser.find_element(By.XPATH, row_path(title) + "//button[@class='delete-task']").click()
    wait_until(browser, EC.invisibility_of_element_located((By.XPATH, row_path(title))))   # true once the row is gone


def test_empty_title_is_not_submitted(browser):
    count_before = len(browser.find_elements(By.CSS_SELECTOR, "li.task"))
    browser.find_element(By.ID, "add-task").click()
    field = browser.find_element(By.ID, "task-title")
    assert browser.execute_script("return arguments[0].validity.valueMissing;", field)   # the browser blocked the form
    assert len(browser.find_elements(By.CSS_SELECTOR, "li.task")) == count_before