import pytest
import chan_stats
import status_check

# @pytest.fixture
# def app():
#     app = create_app()
#     return app


def test_check_status():
    t = chan_stats.ChanStats("test", "google.com")
    status = t.check_status()
    assert status == 200


@pytest.fixture
def app():
    return status_check.app


def test_show_stats():
    result = status_check.show_stats("kara")
    assert result is not None
