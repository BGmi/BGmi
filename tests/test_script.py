from bgmi.script import ScriptBase


class Script(ScriptBase):
    class Model(ScriptBase.Model):
        bangumi_name = "TEST_BANGUMI"
        cover = ""
        update_time = "Mon"

    def get_download_url(self):
        # fetch and return dict
        resp = {
            1: "http://example.com/Bangumi/1/1.mp4",
            2: "http://example.com/Bangumi/1/2.torrent",
            3: "http://example.com/Bangumi/1/3.mp4",
        }

        ret = {}
        for k, v in resp.items():
            ret[int(k)] = v

        return ret


if __name__ == "__main__":  # pragma: no cover
    s = Script()
    s.get_download_url()
