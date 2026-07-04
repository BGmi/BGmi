from unittest import mock

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
