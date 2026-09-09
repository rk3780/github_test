import pytest
from circle_area import circlearea


def test_circle_area():
    assert circlearea(0) == pytest.approx(0, rel=0.01)
    assert circlearea(1) == pytest.approx(3.14, rel=0.01)    
    assert circlearea(2) == pytest.approx(12.56, rel=0.01)
    assert circlearea(3) == pytest.approx(28.26, rel=0.01)
    assert circlearea(5) == pytest.approx(78.5, rel=0.01)
    assert circlearea(10) == pytest.approx(314.0, rel=0.01)
    assert circlearea(100) == pytest.approx(31400.0, rel=0.01)
    assert circlearea(50) == pytest.approx(7850.0, rel=0.01)
    assert circlearea(25) == pytest.approx(1963.5, rel=0.01)
    assert circlearea(12.5) == pytest.approx(490.875, rel=0.01)
    assert circlearea(7.5) == pytest.approx(176.625, rel=0.01)
    assert circlearea(15) == pytest.approx(706.5, rel=0.01)