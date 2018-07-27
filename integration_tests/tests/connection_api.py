import time
import requests
import os
import logging

logging.basicConfig(level=logging.WARNING)


def delete_old_database():
    dirname = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    filename = 'example_project/example_project/db.sqlite3'
    path = os.path.abspath(os.path.join(dirname, filename))

    try:
        os.remove(path)
        logging.debug("Database file in example_project DELETED!")
    except OSError:
        logging.debug("No database file found.")


def obtain_csrftoken(session):
    """
    A CSRF cookie token is required in order to not get a 403 Forbidden response by
    the post to the inputs.
    :return: String representing the token.
    """

    return session.cookies['csrftoken']


def create_session():
    """
    A integration test utility to create a browser session request for a single test.
    :return: A session object for requests.
    """

    return requests.Session()


def send_get_request(session, url):
    """
    Attempts to send a GET to the url. Server is already up as the test should
    be calling the `is_server_healthy()` function before calling this.

    :param session: Object representing the browser session.
    :param url: String, containing 'http://', with the URL of the target URL.
    :return: Response of GET.
    """
    response = None

    logging.debug("Attempting a GET request for the provided URL...")
    try:
        response = session.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.debug(e)

    return response


def send_post_request(session, url, data):
    """
    Attempts to send a POST to the url. Server is already up as the test should
    be calling the `is_server_healthy()` function before calling this.

    :return: Response of POST.
    """
    response = None

    logging.debug("Attempting a POST request for the provided URL...")

    try:
        response = session.post(url, data=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.debug(e)

    return response


def server_is_healthy(url):
    """
    Function will only return True when the param URL returns a 2xx code. After
    45 seconds, the check assumes a timeout.
    :param url: http URL for the address to poll.
    :return: boolean value to indicate result.
    """

    logging.debug("Checking if the server is healthy...")
    for _ in range(45):
        try:
            status_code = requests.get(url).status_code
            if status_code // 100 == 2:
                return True
        except requests.exceptions.RequestException:
            pass

        time.sleep(1)
    return False


def _log_in_as_a_superuser():
    """
    A private wrapper function for all the utilities that will
    log a user in with the correct credentials and take care of
    all CSRF token exchange.
    """
    url = 'http://localhost:8000/aimmo/accounts/login/'
    assert(server_is_healthy(url))

    logging.debug("Creating session...")
    session = create_session()

    send_get_request(session, url)

    logging.debug("Obtaining CSRF Token...")
    csrftoken = obtain_csrftoken(session)

    login_info = {
        'username': 'admin',
        'password': 'admin',
        'csrfmiddlewaretoken': csrftoken,
    }

    logging.debug("Sending post response...")

    response = send_post_request(session, url, login_info)
    assert(response.status_code == 200)

    return csrftoken, session


def create_custom_game_default_settings(name):
    """
    Sends an appropriate POST request to create a game with a
    given name, using default settings provided.
    """
    csrftoken, session = _log_in_as_a_superuser()

    host = 'http://localhost:8000/'
    url = host + 'aimmo/games/new/'

    csrftoken = session.cookies['csrftoken']

    data = {
        "csrfmiddlewaretoken": csrftoken,
        "name": name,
    }

    headers = {'X-CSRFToken': csrftoken, 'Referer': 'http://localhost:8000/aimmo/accounts/login/'}

    response = session.post(url, data=data, headers=headers)

    return response, session
