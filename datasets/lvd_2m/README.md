# LVD-2M

- 官方仓库：https://github.com/SilentView/LVD-2M（NeurIPS 2024 D&B Track）
- 难度：★★★（逻辑最绕）

## 获取方式

官方只直接公开了 100 个随机采样视频用于试用/demo。完整 2M 数据集实际是
**三个来源的组合**：YouTube / HDVG（即 HD-VG-130M） / WebVid，仓库给的是
annotation 文件（含 `raw_caption` 等字段）+ 每条记录标注了它属于哪个 split。

## TODO

1. 下载官方 annotation 文件，按 `split` 字段（youtube / hdvg / webvid）拆成三批任务。
2. **YouTube 那批**：直接复用 `common/youtube_fetch.py`。
3. **HDVG 那批**：如果 `datasets/hd_vg_130m/` 已经下载过对应视频，靠
   `common/dedupe.py` 的 MD5 查重自动跳过，不要重新下载 —— 但注意 MD5 去重是
   下载完之后才能算出来的，所以还是得先尝试下载/或直接查 `hd_vg_130m` 已下载记录里
   有没有相同 video_id，有的话直接建软链接，不发起下载请求。
4. **WebVid 那批**：WebVid 官方源已知长期不稳定（原始 WebVid 下载渠道多次变更/失效），
   这部分难度可能高于其他部分，建议单独评估，必要时向客户说明这部分到手率会偏低。
5. 异常视频可联系作者邮箱（见官方仓库联系方式）要求处理，不要自己各种猜测重试。

## 风险提示

这是清单里对客户最需要提前说明"到手率可能明显低于其他数据集"的一个，
尤其 WebVid 来源部分建议提前预期管理。
