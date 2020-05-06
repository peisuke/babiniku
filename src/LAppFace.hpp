#pragma once

class LAppFace
{
public:
    LAppFace();

    virtual ~LAppFace();

    void Update();
    const double GetX();
    const double GetY();
    const double GetZ();
    const double GetVolume();

private:
    double _dirX;
    double _dirY;
    double _dirZ;
    double _sound;
};

