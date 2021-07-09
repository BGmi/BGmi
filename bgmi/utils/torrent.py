import hashlib

import bencoding


def get_info_hash_from_content(content: bytes) -> str:
    data = bencoding.bdecode(content)
    return hashlib.sha1(bencoding.bencode(data[b"info"])).hexdigest()


def get_info_hash_from_torrent(fs: str) -> str:
    with open(fs, "rb") as f:
        content = f.read()
    try:
        return get_info_hash_from_content(content)
    except bencoding.decoder.DecoderError:
        print(fs, flush=True)
        raise
