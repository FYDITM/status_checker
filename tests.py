import pytest
import chans_settings
import chan_stats


# @pytest.fixture
# def app():
#     app = create_app()
#     return app


def test_check_status():
    t = chan_stats.ChanStats("test", "google.com")
    status = t.check_status()
    assert status == 200


def test_chan_list():
    chans = chans_settings.chans
    assert len(chans) > 2
    for chan in chans:
        assert chan.users_online == "n/a"

# @pytest.fixture
# def app():
#     return status_check.app


# def test_show_stats():
#     result = status_check.show_stats("kara")
#     status_check.stop_checking()
#     assert result is not None


# def test_kopara():
#     global running
#     result = status_check.kopara()
#     status_check.stop_checking()
#     assert result is not None
