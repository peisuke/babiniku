/**
 * Copyright(c) Live2D Inc. All rights reserved.
 *
 * Use of this source code is governed by the Live2D Open Software license
 * that can be found at https://www.live2d.com/eula/live2d-open-software-license-agreement_en.html.
 */

#include "LAppView.hpp"
#include <math.h>
#include <string>
#include "LAppPal.hpp"
#include "LAppDelegate.hpp"
#include "LAppLive2DManager.hpp"
#include "LAppTextureManager.hpp"
#include "LAppDefine.hpp"
#include "TouchManager.hpp"
#include "LAppSprite.hpp"
#include "LAppModel.hpp"

#include <Rendering/OpenGL/CubismOffscreenSurface_OpenGLES2.hpp>
#include <Rendering/OpenGL/CubismRenderer_OpenGLES2.hpp>

using namespace std;
using namespace LAppDefine;

LAppView::LAppView():
    _programId(0),
    _back(NULL),
    _renderSprite(NULL),
    _renderTarget(SelectTarget_None)
{
    _clearColor[0] = 1.0f;
    _clearColor[1] = 1.0f;
    _clearColor[2] = 1.0f;
    _clearColor[3] = 0.0f;

    // デバイス座標からスクリーン座標に変換するための
    _deviceToScreen = new CubismMatrix44();

    // 画面の表示の拡大縮小や移動の変換を行う行列
    _viewMatrix = new CubismViewMatrix();
}

LAppView::~LAppView()
{
    _renderBuffer.DestroyOffscreenFrame();
    delete _renderSprite;

    delete _viewMatrix;
    delete _deviceToScreen;
    delete _back;
}

void LAppView::Initialize()
{
    int width, height;
    glfwGetWindowSize(LAppDelegate::GetInstance()->GetWindow(), &width, &height);

    if(width==0 || height==0)
    {
        return;
    }

    float ratio = static_cast<float>(height) / static_cast<float>(width);
    float left = ViewLogicalLeft;
    float right = ViewLogicalRight;
    float bottom = -ratio;
    float top = ratio;

    _viewMatrix->SetScreenRect(left, right, bottom, top); // デバイスに対応する画面の範囲。 Xの左端, Xの右端, Yの下端, Yの上端

    float screenW = fabsf(left - right);
    _deviceToScreen->LoadIdentity();
    _deviceToScreen->ScaleRelative(screenW / width, -screenW / width);
    _deviceToScreen->TranslateRelative(-width * 0.5f, -height * 0.5f);

    // 表示範囲の設定
    _viewMatrix->SetMaxScale(ViewMaxScale); // 限界拡大率
    _viewMatrix->SetMinScale(ViewMinScale); // 限界縮小率

    // 表示できる最大範囲
    _viewMatrix->SetMaxScreenRect(
        ViewLogicalMaxLeft,
        ViewLogicalMaxRight,
        ViewLogicalMaxBottom,
        ViewLogicalMaxTop
    );
}

void LAppView::Render()
{
    _back->Render();

    LAppLive2DManager* Live2DManager = LAppLive2DManager::GetInstance();

    // Cubism更新・描画
    Live2DManager->OnUpdate();
}

void LAppView::InitializeSprite()
{
    _programId = LAppDelegate::GetInstance()->CreateShader();

    int width, height;
    glfwGetWindowSize(LAppDelegate::GetInstance()->GetWindow(), &width, &height);

    LAppTextureManager* textureManager = LAppDelegate::GetInstance()->GetTextureManager();
    const string resourcesPath = LAppDelegate::GetInstance()->GetRootDirectory() + ResourcesPath;

    string imageName = BackImageName;
    LAppTextureManager::TextureInfo* backgroundTexture = textureManager->CreateTextureFromPngFile(resourcesPath + imageName);

    float x = width * 0.5f;
    float y = height * 0.5f;
    float fWidth = static_cast<float>(backgroundTexture->width * 2.0f);
    float fHeight = static_cast<float>(height) * 0.95f;
    _back = new LAppSprite(x, y, fWidth, fHeight, backgroundTexture->id, _programId);

    // 画面全体を覆うサイズ
    x = width * 0.5f;
    y = height * 0.5f;
    _renderSprite = new LAppSprite(x, y, static_cast<float>(width), static_cast<float>(height), 0, _programId);
}

void LAppView::ResizeSprite()
{
    LAppTextureManager* textureManager = LAppDelegate::GetInstance()->GetTextureManager();
    if (!textureManager)
    {
        return;
    }

    // 描画領域サイズ
    int width, height;
    glfwGetWindowSize(LAppDelegate::GetInstance()->GetWindow(), &width, &height);

    float x = 0.0f;
    float y = 0.0f;
    float fWidth = 0.0f;
    float fHeight = 0.0f;

    if (_back)
    {
        GLuint id = _back->GetTextureId();
        LAppTextureManager::TextureInfo* texInfo = textureManager->GetTextureInfoById(id);
        if (texInfo)
        {
            x = width * 0.5f;
            y = height * 0.5f;
            fWidth = static_cast<float>(texInfo->width * 2);
            fHeight = static_cast<float>(height) * 0.95f;
            _back->ResetRect(x, y, fWidth, fHeight);
        }
    }
}
