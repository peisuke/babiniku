/**
 * Copyright(c) Live2D Inc. All rights reserved.
 *
 * Use of this source code is governed by the Live2D Open Software license
 * that can be found at https://www.live2d.com/eula/live2d-open-software-license-agreement_en.html.
 */

#include "LAppLive2DManager.hpp"
#include <string>
#include <iostream>
#include <GL/glew.h>
#include <GLFW/glfw3.h>
#include <Rendering/CubismRenderer.hpp>
#include "LAppPal.hpp"
#include "LAppDefine.hpp"
#include "LAppDelegate.hpp"
#include "LAppModel.hpp"
#include "LAppView.hpp"
#include "LAppSprite.hpp"

using namespace Csm;
using namespace LAppDefine;
using namespace std;

namespace {
    LAppLive2DManager* s_instance = NULL;

    void FinishedMotion(ACubismMotion* self)
    {
        LAppPal::PrintLog("Motion Finished: %x", self);
    }
}

LAppLive2DManager* LAppLive2DManager::GetInstance()
{
    if (s_instance == NULL)
    {
        s_instance = new LAppLive2DManager();
    }

    return s_instance;
}

void LAppLive2DManager::ReleaseInstance()
{
    if (s_instance != NULL)
    {
        delete s_instance;
    }

    s_instance = NULL;
}

LAppLive2DManager::LAppLive2DManager()
    : _viewMatrix(NULL)
    , _sceneIndex(0)
{
    CreateScene(_sceneIndex);
}

LAppLive2DManager::~LAppLive2DManager()
{
    ReleaseAllModel();
}

void LAppLive2DManager::ReleaseAllModel()
{
    for (csmUint32 i = 0; i < _models.GetSize(); i++)
    {
        delete _models[i];
    }

    _models.Clear();
}

LAppModel* LAppLive2DManager::GetModel(csmUint32 no) const
{
    if (no < _models.GetSize())
    {
        return _models[no];
    }

    return NULL;
}

void LAppLive2DManager::OnUpdate() const
{
    CubismMatrix44 projection;
    int width, height;
    glfwGetWindowSize(LAppDelegate::GetInstance()->GetWindow(), &width, &height);
    projection.Scale(1.0f, static_cast<float>(width) / static_cast<float>(height));
    projection.ScaleRelative(4.0f, 4.0f);
    projection.TranslateRelative(0, -0.3);

    if (_viewMatrix != NULL)
    {
        projection.MultiplyByMatrix(_viewMatrix);
    }

    const CubismMatrix44    saveProjection = projection;
    csmUint32 modelCount = _models.GetSize();
    for (csmUint32 i = 0; i < modelCount; ++i)
    {
        LAppModel* model = GetModel(i);
        projection = saveProjection;

        model->Update();
        model->Draw(projection);///< 参照渡しなのでprojectionは変質する
    }
}

void LAppLive2DManager::CreateScene(Csm::csmInt32 index)
{
    _sceneIndex = index;
    if (DebugLogEnable)
    {
        LAppPal::PrintLog("[APP]model index: %d", _sceneIndex);
    }

    // ModelDir[]に保持したディレクトリ名から
    // model3.jsonのパスを決定する.
    // ディレクトリ名とmodel3.jsonの名前を一致させておくこと.
    std::string model = ModelDir[index];
    std::string modelPath = LAppDelegate::GetInstance()->GetRootDirectory() + ResourcesPath + model + "/";
    std::string modelJsonName = ModelDir[index];
    modelJsonName += ".model3.json";
    ReleaseAllModel();
    _models.PushBack(new LAppModel());
    _models[0]->LoadAssets(modelPath.c_str(), modelJsonName.c_str());
}

csmUint32 LAppLive2DManager::GetModelNum() const
{
    return _models.GetSize();
}
