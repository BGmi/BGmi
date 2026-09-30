from unittest import mock

import pytest

from bgmi.website.mikan import Mikanani

MIKAN_BANGUMI_HTML = """
<div class="pull-left leftbar-container">
  <img src="/images/subscribed-badge.svg" class="subscribed-badge" />
  <div class="bangumi-poster" style="background-image: url('/images/Bangumi/202604/c68609a0.jpg?width=400&height=560&format=webp');"></div>
  <p class="bangumi-title">大欺诈师</p>
  <p class="bangumi-info">更新时间：星期一</p>
</div>
<div class="leftbar-nav">
  <ul><li><a data-anchor="#34">极影字幕社</a></li></ul>
</div>
<div class="central-container">
  <div id="34"></div>
  <div class="episode-table">
    <table>
      <tr><th>title</th><th>download</th><th>size</th><th>time</th></tr>
      <tr>
        <td></td>
        <td>
          <a class="magnet-link-wrap">大欺诈师 01</a>
          <a class="magnet-link" data-clipboard-text="magnet:?xt=urn:btih:1"></a>
        </td>
        <td></td>
        <td>2026/07/04 12:00</td>
      </tr>
    </table>
  </div>
</div>
"""


def test_mikan_fetch_single_bangumi_includes_cover():
    with mock.patch("bgmi.website.mikan.get_text", return_value=MIKAN_BANGUMI_HTML):
        bangumi = Mikanani().fetch_single_bangumi("2242")

    assert bangumi is not None
    assert bangumi.cover == "https://mikanani.me/images/Bangumi/202604/c68609a0.jpg"


MIKAN_GREY_CALENDAR = """
<div class="sk-bangumi" data-dayofweek="1"><ul>
<li><span class="b-lazy greyout" data-bangumiid="123" data-src="/images/upcoming.jpg?width=400"></span>
<div class="an-info"><div class="date-text">此番组下暂无作品</div>
<div class="date-text" title="待播番剧">待播番剧</div></div></li>
<li><span data-src="/images/current.jpg"></span>
<a href="/Home/Bangumi/456" title="已上线番剧">已上线番剧</a></li>
</ul></div>
<div class="sk-bangumi" data-dayofweek="7"><ul>
<li><span class="greyout" data-bangumiid="789" data-src="/images/movie.jpg"></span>
<div class="an-info"><div class="date-text" title="剧场版">剧场版</div></div></li>
</ul></div>
"""


def test_calendar_includes_grey_entries_but_still_skips_movies():
    with mock.patch("bgmi.website.mikan.get_text", return_value=MIKAN_GREY_CALENDAR):
        entries = Mikanani().fetch_bangumi_calendar()
    assert [(b.id, b.name, b.update_day) for b in entries] == [("123", "待播番剧", "Mon"), ("456", "已上线番剧", "Mon")]
    assert entries[0].cover == "https://mikanani.me/images/upcoming.jpg"


def test_grey_detail_redirect_has_no_episodes():
    with mock.patch("bgmi.website.mikan.get_text", return_value=MIKAN_GREY_CALENDAR):
        website = Mikanani()
        assert website.fetch_single_bangumi("123") is None
        assert website.fetch_episode_of_bangumi("123") == []


def test_missing_detail_is_not_silently_ignored():
    with mock.patch("bgmi.website.mikan.get_text", return_value=MIKAN_GREY_CALENDAR):
        with pytest.raises(AssertionError, match="Central container"):
            Mikanani().fetch_episode_of_bangumi("999")


@pytest.mark.usefixtures("_ensure_data")
def test_grey_entry_can_be_subscribed_and_wait_for_resources():
    from bgmi.lib import controllers
    from bgmi.lib.table import Bangumi

    website = Mikanani()
    with mock.patch("bgmi.website.mikan.get_text", return_value=MIKAN_GREY_CALENDAR):
        website.fetch()
        assert controllers.add("待播番剧")["status"] == "success"
        assert website.get_maximum_episode(Bangumi.get(Bangumi.id == "123")) == []
