"""app 폴더(index.html 등)를 감싸는 안드로이드 프로젝트를 만든다.
usage: python3 build_project.py APP_DIR OUT_DIR PRJ-0078 "앱 이름"
"""
import os, re, shutil, sys

app_dir, out_dir, prj, name = sys.argv[1:5]
num = re.sub(r"\D", "", prj) or "0"
pkg = f"com.jeongjihyun.prj{num}"
if os.path.exists(out_dir):
    shutil.rmtree(out_dir)
main = os.path.join(out_dir, "app/src/main")
java_dir = os.path.join(main, "java", *pkg.split("."))
os.makedirs(java_dir)
shutil.copytree(app_dir, os.path.join(main, "assets"))
if not os.path.exists(os.path.join(main, "assets", "index.html")):
    sys.exit("index.html 이 없습니다")

def w(path, text):
    with open(os.path.join(out_dir, path) if not path.startswith("/") else path, "w", encoding="utf-8") as f:
        f.write(text)

w("settings.gradle", """pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositories { google(); mavenCentral() }
}
rootProject.name = "wrapper"
include ':app'
""")
w("build.gradle", "plugins { id 'com.android.application' version '8.5.2' apply false }\n")
w("gradle.properties", "org.gradle.jvmargs=-Xmx2g\nandroid.useAndroidX=false\n")
w("app/build.gradle", f"""plugins {{ id 'com.android.application' }}
android {{
    namespace '{pkg}'
    compileSdk 34
    defaultConfig {{
        applicationId '{pkg}'
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName '1.0'
    }}
    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }}
}}
""")
safe = name.replace("&", "&amp;").replace("<", "&lt;").replace('"', "")
w("app/src/main/AndroidManifest.xml", f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application android:label="{safe}" android:allowBackup="false">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>
""")
w(os.path.join(java_dir, "MainActivity.java"), f"""package {pkg};

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity {{
    private WebView web;

    @Override
    protected void onCreate(Bundle b) {{
        super.onCreate(b);
        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(false);
        web.setWebViewClient(new WebViewClient());
        setContentView(web);
        web.loadUrl("file:///android_asset/index.html");
    }}

    @Override
    public void onBackPressed() {{
        if (web.canGoBack()) web.goBack(); else super.onBackPressed();
    }}
}}
""")
print("OK", pkg)
