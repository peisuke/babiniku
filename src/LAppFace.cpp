#include <string>
#include <iostream>
#include <cstring>

#include <curl/curl.h>
#include "picojson.h"

#include "LAppFace.hpp"

size_t callBackFunk(char* ptr, size_t size, size_t nmemb, std::string* stream)
{
    int realsize = size * nmemb;
    stream->append(ptr, realsize);
    return realsize;
}

std::string URLGetProc(const char url[])
{
    CURL *curl;
    CURLcode res;
    curl = curl_easy_init();
    std::string chunk;

    if (curl)
        {
        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_HTTPGET, 1);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, callBackFunk);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, (std::string*)&chunk);
        curl_easy_setopt(curl, CURLOPT_PROXY, "");
        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);
        }
    if (res != CURLE_OK) {
      std::cout << "curl error" << std::endl;
      return "";
    }

    return chunk;
}

LAppFace::LAppFace()
  : _dirX(0), _dirY(0), _dirZ(0), _sound(0)
{
}

LAppFace::~LAppFace()
{
}

void LAppFace::Update()
{
  picojson::value json_data;
  char url_target[] = "http://127.0.0.1:5000/";

  std::string str_out = URLGetProc(url_target);

  const std::string err = picojson::parse(json_data, str_out);
  if (err.empty() == false) {
      return;
  }

  picojson::object& obj = json_data.get<picojson::object>();
  
  picojson::array& face = obj["face"].get<picojson::array>();
  if (face.size() > 0) {
    _dirX = face[0].get<double>();
    _dirY = face[1].get<double>();
    _dirZ = face[2].get<double>();
  }
  _sound = obj["sound"].get<double>();
}

const double LAppFace::GetX()
{
  return _dirX;
}

const double LAppFace::GetY()
{
  return _dirY;
}

const double LAppFace::GetZ()
{
  return _dirZ;
}

const double LAppFace::GetVolume()
{
  return _sound;
}
