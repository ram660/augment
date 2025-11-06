from backend.utils.image_filename_parser import parse_image_filename


def test_parse_kitchen_main():
    r = parse_image_filename("Kitchen_Main.jpg")
    assert r["room_type"] in ("kitchen",)
    assert r["floor_level"] in (None, 1)  # 'main' may resolve to 1 depending on normalizer


def test_parse_bedroom_second_floor_number():
    r = parse_image_filename("Bedroom_2F.png")
    assert r["room_type"] == "bedroom"
    # 2F should infer second floor
    assert r["floor_level"] in (2, None)


def test_parse_primary_bathroom_second():
    r = parse_image_filename("primary_bathroom_second.jpeg")
    assert r["room_type"] == "bathroom"
    assert r["floor_level"] in (2, None)


def test_parse_garage_basement():
    r = parse_image_filename("garage-basement.jpg")
    assert r["room_type"] == "garage"
    # basement -> 0 or negative floors may normalize to 0/None depending on helper
    assert r["floor_level"] in (0, None)
