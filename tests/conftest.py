def pytest_addoption(parser):
    parser.addoption("--username", action="store")
    parser.addoption("--password", action="store")