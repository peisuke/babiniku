# フルスクラッチバ美肉プロジェクト

## 概要

諸々のツールをなるべく使わずにリアルタイムで美少女になってZoomでWebミーティングをするためのプロジェクト。
本プロジェクトの一部は、[CubismSDKおよびサンプルモデル](https://github.com/Live2D/CubismNativeSamples)を利用してており、
`resouces`、`cubism`および`src`ディレクトリ以下は、Cubism SDK Release Licenseに従います。

## 構成

![image](https://user-images.githubusercontent.com/14243883/81827836-1dfbaf00-9574-11ea-85b8-835556957d53.png)

※CamTwistは使えなくなったので、現在ではOBS Studioを利用しています。

## 必要環境およびライブラリ

## ビルド

```
$ mkdir build
$ cd build
$ cmake .. && make
```

## 利用方法

下記３つを立ち上げた上で、ZoomとCamTwistを設定を行う。

### 音声変換ツールの立ち上げ

```
$ cd script
$ python voice_converter.py
```

### 顔認識サーバの立ち上げ

```
$ cd server
$ python app.py
```

### 美少女を表示

```
$ cd build/bin
$ ./Demo
```

### Zoom連携

- ~CamTwist~OBSを開き、Desktop+から`Confine to Application Window`をチェック、`Select from existing windows`の中からDemoを選択
- Zoomの音声入力をBlackholeに、ビデオ入力をCamTwistに設定

## 画面イメージ

![image](https://user-images.githubusercontent.com/14243883/81830782-7aac9900-9577-11ea-87fd-accfd9a5cca2.png)

