"""ASS / SRT 생성."""
import re


def ass_color(hex_rgb):
    """#RRGGBB → ASS &H00BBGGRR"""
    h = hex_rgb.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H00{b}{g}{r}".upper().replace("&H", "&H")


def ass_time(sec):
    cs = int(round(sec * 100))
    h, cs = divmod(cs, 360000); m, cs = divmod(cs, 6000); s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def srt_time(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def style_line(s):
    return ("Style: {id},{font},{size},{pc},{pc},{oc},&H00000000,{b},0,0,0,100,100,0,0,1,{ol},{sh},{al},40,40,{mv},1"
            .format(id=s["id"], font=s["font"], size=s["size"], pc=ass_color(s["color"]),
                    oc=ass_color(s["outline_color"]), b=-1 if s["bold"] else 0, ol=s["outline"],
                    sh=s["shadow"], al=s["alignment"], mv=s["margin_v"]))


def build_ass(styles, resolution, seconds_per=3.0, one_style_only=None):
    chosen = [s for s in styles if one_style_only in (None, s["id"])]
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {resolution[0]}", f"PlayResY: {resolution[1]}",
             "WrapStyle: 0", "", "[V4+ Styles]",
             "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,"
             "Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding"]
    lines += [style_line(s) for s in chosen]
    lines += ["", "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
    t = 0.0
    for s in chosen:
        fade = f"{{\\fad({s['fade_in_ms']},{s['fade_out_ms']})}}" if (s["fade_in_ms"] or s["fade_out_ms"]) else ""
        text = s["sample_text"].replace("\n", "\\N")
        lines.append(f"Dialogue: 0,{ass_time(t)},{ass_time(t + seconds_per)},{s['id']},,0,0,0,,{fade}{text}")
        t += seconds_per
    return "\n".join(lines) + "\n"


def build_srt(styles, seconds_per=3.0, one_style_only=None):
    chosen = [s for s in styles if one_style_only in (None, s["id"])]
    out, t = [], 0.0
    for i, s in enumerate(chosen, start=1):
        out.append(f"{i}\n{srt_time(t)} --> {srt_time(t + seconds_per)}\n{s['sample_text']}\n")
        t += seconds_per
    return "\n".join(out)


ASS_TIME = re.compile(r"^\d:\d{2}:\d{2}\.\d{2}$")
SRT_TIME = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3}$")
