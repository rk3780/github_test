import pytest
from circle_area import circlearea


def test_circle_area():
    assert circlearea(0) == 0
    assert circlearea(1) == 3.14    
    assert circlearea(2) == 12.56
    assert circlearea(3) == 28.26
    assert circlearea(5) == 78.5
    assert circlearea(10) == 314.0
    assert circlearea(100) == 31400.0
    assert circlearea(50) == 7850.0
    assert circlearea(25) == 1963.5
    assert circlearea(12.5) == 490.875
    assert circlearea(7.5) == 176.625
    assert circlearea(15) == 706.5