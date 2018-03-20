import pytest
import chans_settings
import chan_stats
import multiprocessing
import concurrent.futures


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
        assert chan.users_online == "n/d"
        assert chan.status == "n/d"


def check_posts(chan):
    post = chan.get_current_post(chan.boards_url + "/b/")
    return chan.name, post


def test_chan_stats():
    chans = chans_settings.chans
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = [executor.submit(c.parse_status) for c in chans]
        output = [r.result() for r in results]
        for c in chans:
            assert c.status is not None
        working_chans = list(filter(lambda c: c.OK, chans))
        dead_chans = list(filter(lambda c: c.OK is False, chans))
        print("działające czany: {0}/{1}".format(len(list(working_chans)), len(chans)))
        print("zdechłe: {0}".format(list(map(lambda x: x.name, dead_chans))))
        users_chans = list(filter(lambda ch: ch.users_online_url is not None, working_chans))
        posts_chans = list(filter(lambda ch: ch.boards is not None, working_chans))
        user_results = [executor.submit(c.check_users_online) for c in users_chans]
        post_results = [executor.submit(check_posts, c) for c in posts_chans]
        users_output = [u.result() for u in user_results]
        posts_output = [p.result() for p in post_results]
        print("czany z userami: {0}".format(len(users_chans)))
        print("czany z postami: {0}".format(len(posts_chans)))

        for c in users_chans:
            print("online na {0}: {1}".format(c.name, c.users_online))
            assert c.users_online != "n/a"
        for p in posts_output:
            print("post id na {0}: {1}".format(*p))
            assert p[1] is not None
        for c in chans:
            print("status {0}: {1}".format(c.name, c.status))
            c.status != "n/a"

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
