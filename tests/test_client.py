from .fixtures import client


def test_connect_client(caplog, client):
    caplog.set_level("DEBUG")

    exception = ""
    try:
        client.start(timeout=1)
    except ConnectionRefusedError as e:
        exception = e

    assert (
        client.connection_status == 0
    ), f"{exception=} Make sure you have a broker running: docker run -it -p1883:1883 emqx/emqx-ee"
