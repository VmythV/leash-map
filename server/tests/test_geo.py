"""Trail downsampling (Douglas-Peucker)."""
from leashmap.geo import douglas_peucker, haversine_m


def test_straight_line_collapses_to_endpoints():
    # 11 collinear points along a meridian -> keep only the two ends
    pts = [(31.0 + i * 0.001, 121.0) for i in range(11)]
    keep = douglas_peucker(pts, epsilon_m=8.0)
    assert keep == [0, 10]


def test_spike_is_preserved():
    # a straight line with one point pushed ~50m east in the middle
    pts = [(31.0 + i * 0.001, 121.0) for i in range(11)]
    pts[5] = (pts[5][0], 121.0 + 0.0006)  # ~57m east at this latitude
    keep = douglas_peucker(pts, epsilon_m=8.0)
    assert 0 in keep and 10 in keep
    assert 5 in keep
    assert len(keep) < len(pts)


def test_small_input_unchanged():
    assert douglas_peucker([(31.0, 121.0)], 8.0) == [0]
    assert douglas_peucker([(31.0, 121.0), (31.1, 121.1)], 8.0) == [0, 1]


def test_haversine_sane():
    # ~111 km per degree of latitude
    d = haversine_m(31.0, 121.0, 32.0, 121.0)
    assert 110_000 < d < 112_000
