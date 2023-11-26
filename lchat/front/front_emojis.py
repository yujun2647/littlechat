import os
import json
from threading import Lock

from lchat.utils.util_path import get_cache_data_filepath

EMOJIS = {
    "People": [
        {
            "key": "slightly_smiling_face",
            "value": "🙂"
        },
        {
            "key": "grinning_face",
            "value": "😀"
        },

        {
            "key": "grimacing_face",
            "value": "😬"
        },
        {
            "key": "smile_sc",
            "value": "🤭"
        },
        {
            "key": "grimacing_face_with_smile_eyes",
            "value": "😁"
        },
        {
            "key": "face_with_tear_of_joy",
            "value": "😂"
        },
        {
            "key": "smiling_face_with_open_mouth",
            "value": "😃"
        },
        {
            "key": "smiling_face_with_open_mouth_eyes",
            "value": "😄"
        },
        {
            "key": "smiling_face_with_open_mouth_cold_sweat",
            "value": "😅"
        },
        {
            "key": "smiling_face_with_open_mouth_hand_tight",
            "value": "😆"
        },
        {
            "key": "smiling_face_with_halo",
            "value": "😇"
        },
        {
            "key": "winking_face",
            "value": "😉"
        },
        {
            "key": "black_smiling_face",
            "value": "😊"
        },
        {
            "key": "silence",
            "value": "🤫"
        },
        {
            "key": "smiling_si",
            "value": "🤤"
        },
        {
            "key": "face_savouring_delicious_food",
            "value": "😋"
        },
        {
            "key": "hugging_face",
            "value": "🤗"
        },
        {
            "key": "smiling_face_star_eyes",
            "value": "🤩"
        },
        {
            "key": "smiling_face_heart_eyes",
            "value": "😍"
        },

        {
            "key": "face_throwing_kiss",
            "value": "😘"
        },
        {
            "key": "kissing_face_with_closed_eyes",
            "value": "😚"
        },
        {
            "key": "124",
            "value": "🥰"
        },
        {
            "key": "125",
            "value": "🥳"
        },
        {
            "key": "confetti_ball",
            "value": "🎊"
        },
        {
            "key": "party_popper",
            "value": "🎉"
        },

        {
            "key": "face_with_tongue_wink_eye",
            "value": "😜"
        },
        {
            "key": "face_with_tongue_closed_eye",
            "value": "😝"
        },
        {
            "key": "123",
            "value": "🥱"
        },
        {
            "key": "sleeping_face",
            "value": "😴"
        },

        {
            "key": "sleeping_symbol",
            "value": "💤"
        },

        {
            "key": "smiling_face_with_sunglasses",
            "value": "😎"
        },

        {
            "key": "thinking_face",
            "value": "🤔"
        },

        {
            "key": "relieved_face",
            "value": "😌"
        },
        {
            "key": "disappointed_face",
            "value": "😞"
        },
        {
            "key": "face_with_rolling_eyes",
            "value": "🙄"
        },
        {
            "key": "flushed_face",
            "value": "😳"
        },

        {
            "key": "worried_face",
            "value": "😟"
        },
        {
            "key": "angry_face",
            "value": "😠"
        },
        {
            "key": "pouting_face",
            "value": "😡"
        },
        {
            "key": "ku",
            "value": "😣"
        },
        {
            "key": "weary_face",
            "value": "😩"
        },
        {
            "key": "face_with_look_of_triumph",
            "value": "😤"
        },

        {
            "key": "126",
            "value": "🥵"
        },
        {
            "key": "127",
            "value": "🥶"
        },
        {
            "key": "128",
            "value": "🥹"
        },
        {
            "key": "132",
            "value": "🥺"
        },

        {
            "key": "face_screaming_in_fear",
            "value": "😱"
        },
        {
            "key": "fearful_face",
            "value": "😨"
        },

        {
            "key": "disappointed_but_relieved_face",
            "value": "😥"
        },

        {
            "key": "face_with_cold_sweat",
            "value": "😓"
        },
        {
            "key": "loudly_crying_face",
            "value": "😭"
        },
        {
            "key": "dizzy_face",
            "value": "😵"
        },
        {
            "key": "zipper_mouth_face",
            "value": "🤐"
        },
        {
            "key": "face_with_medical_mask",
            "value": "😷"
        },

        {
            "key": "130",
            "value": "🤧"
        },

        {
            "key": "pu",
            "value": "🤮"
        },
        {
            "key": "face_with_thermometer",
            "value": "🤒"
        },
        {
            "key": "face_with_head_bandage",
            "value": "🤕"
        },

        {
            "key": "pile_of_poo",
            "value": "💩"
        },
        {
            "key": "smiling_face_with_horns",
            "value": "😈"
        },
        {
            "key": "imp",
            "value": "👿"
        },
        {
            "key": "japanese_ogre",
            "value": "👹"
        },
        {
            "key": "japanese_goblin",
            "value": "👺"
        },
        {
            "key": "skull",
            "value": "💀"
        },
        {
            "key": "ghost",
            "value": "👻"
        },
        {
            "key": "extra_terrestrial_alien",
            "value": "👽"
        },
        {
            "key": "robot_face",
            "value": "🤖"
        },
        {
            "key": "smiling_cat_face_open_mouth",
            "value": "😺"
        },
        {
            "key": "grinning_cat_face_smile_eyes",
            "value": "😸"
        },
        {
            "key": "cat_face_tears_of_joy",
            "value": "😹"
        },
        {
            "key": "smiling_cat_face_heart_shaped_eyes",
            "value": "😻"
        },
        {
            "key": "cat_face_wry_smile",
            "value": "😼"
        },
        {
            "key": "kissing_cat_face_closed_eyes",
            "value": "😽"
        },
        {
            "key": "weary_cat_face",
            "value": "🙀"
        },
        {
            "key": "crying_cat_face",
            "value": "😿"
        },
        {
            "key": "pouting_cat_face",
            "value": "😾"
        },
        {
            "key": "person_both_hand_celebration",
            "value": "🙌"
        },

        {
            "key": "clapping_hand",
            "value": "👏"
        },
        {
            "key": "waving_hands",
            "value": "👋"
        },
        {
            "key": "thumbs_up",
            "value": "👍"
        },
        {
            "key": "666",
            "value": "🤙"
        },
        {
            "key": "thumbs_down",
            "value": "👎"
        },
        {
            "key": "fist_hand",
            "value": "👊"
        },
        {
            "key": "raised_fist",
            "value": "✊"
        },
        {
            "key": "ok_hand",
            "value": "👌"
        },
        {
            "key": "flexed_biceps",
            "value": "💪"
        },
        {
            "key": "folded_hands",
            "value": "🙏"
        },
        {
            "key": "eyes",
            "value": "👀"
        },

        {
            "key": "kiss_mark",
            "value": "💋"
        },

    ],

    "Nature": [
        {
            "key": "dog_face",
            "value": "🐶"
        },
        {
            "key": "cat_face",
            "value": "🐱"
        },
        {
            "key": "pig_face",
            "value": "🐷"
        },

        {
            "key": "see_no_evil_monkey",
            "value": "🙈"
        },
        {
            "key": "hear_no_evil_monkey",
            "value": "🙉"
        },
        {
            "key": "speak_no_evil_monkey",
            "value": "🙊"
        },
        {
            "key": "monkey",
            "value": "🐒"
        },
        {
            "key": "sheep",
            "value": "🐑"
        },
        {
            "key": "dog",
            "value": "🐕"
        },

        {
            "key": "maple_leaf",
            "value": "🍁"
        },
        {
            "key": "hibiscus",
            "value": "🌺"
        },
        {
            "key": "sunflower",
            "value": "🌻"
        },
        {
            "key": "rose",
            "value": "🌹"
        },
        {
            "key": "tulip",
            "value": "🌷"
        },
        {
            "key": "blossom",
            "value": "🌼"
        },
        {
            "key": "cherry_blossom",
            "value": "🌸"
        },
        {
            "key": "bouquet",
            "value": "💐"
        },
        {
            "key": "full_moon",
            "value": "🌕"
        },

        {
            "key": "fire",
            "value": "🔥"
        },
        {
            "key": "collision",
            "value": "💥"
        },
    ],
    "Symbols": [
        {
            "key": "broken_heart",
            "value": "💔"
        },
        {
            "key": "two_hearts",
            "value": "💕"
        },
        {
            "key": "beating_heart",
            "value": "💓"
        },
        {
            "key": "growing_heart",
            "value": "💗"
        },
        {
            "key": "sparkling_heart",
            "value": "💖"
        },
        {
            "key": "heart_with_arrow",
            "value": "💘"
        },
        {
            "key": "anger_symbol",
            "value": "💢"
        },

        {
            "key": "thought_balloon",
            "value": "💭"
        },
        {
            "key": "speech_balloon",
            "value": "💬"
        }
    ]
}


def get_all_emojis():
    all_emojis = []
    for emojis in EMOJIS.values():
        for emoji in emojis:
            all_emojis.append(emoji["value"])
    return all_emojis


class FavoriteEmoji(object):
    FAVORITE_NUM = 6

    _CACHE_FAVORITES = {

    }

    def __init__(self, username):
        self.cache_filepath = get_cache_data_filepath(
            folder="favorite_emoji",
            filename=f"{username}.json")
        self._load_cache_favorites()
        self.op_lock = Lock()

    def _load_cache_favorites(self):
        if os.path.exists(self.cache_filepath):
            with open(self.cache_filepath, "r") as fp:
                self._CACHE_FAVORITES = json.load(fp)
            return

        with open(self.cache_filepath, "w") as fp:
            json.dump({}, fp)

    def _update_cache_favorites(self):
        with open(self.cache_filepath, "w") as fp:
            json.dump(self._CACHE_FAVORITES, fp)

    def update_favorites(self, emoji_update: dict):
        if not emoji_update:
            return

        for emoji, count in emoji_update.items():
            if emoji not in self._CACHE_FAVORITES:
                self._CACHE_FAVORITES[emoji] = 0
            self._CACHE_FAVORITES[emoji] += count

        if len(self._CACHE_FAVORITES) == 1:
            for key in self._CACHE_FAVORITES.keys():
                self._CACHE_FAVORITES[key] = 4
            return

        s_keys = sorted(self._CACHE_FAVORITES.keys(),
                        key=lambda k: self._CACHE_FAVORITES[k])

        i = 1
        while i < len(s_keys):
            last_key, this_key = s_keys[i - 1: i + 1]
            last_count = self._CACHE_FAVORITES[last_key]
            this_count = self._CACHE_FAVORITES[this_key]
            if this_count - last_count > 3:
                self._CACHE_FAVORITES[this_key] = last_count + 3

            i += 1

        self._update_cache_favorites()

    @property
    def favorite_emojis(self) -> list:
        if not self._CACHE_FAVORITES:
            return []
        emojis = (list(self._CACHE_FAVORITES.keys()))
        emojis.sort(key=lambda key: self._CACHE_FAVORITES[key], reverse=True)
        return emojis


if __name__ == "__main__":
    tt = FavoriteEmoji("test")
    print('debug')
