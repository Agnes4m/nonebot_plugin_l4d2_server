"""关键词屏蔽 + 敏感词打码（README「屏蔽与关键词」方案 4）。

两类规则，在 A2S 结果和输出之间生效：

- ``config.l4_block_keywords``（正则，不区分大小写）：精确屏蔽。服务器名命中
  则整台不出现在组查询、查人、tj/zl/kl 等结果里，单服 / connect 查询只回
  「已被屏蔽」；玩家名命中只隐藏该玩家，人数仍按 A2S 上报。非法正则记一条
  警告后跳过，不影响其它关键词。
- 敏感词库：宽泛过滤。命中的词替换成 ``*``，服务器和玩家照常显示——词库里
  难免混着常用词，打码比整台隐藏温和。来源是包内 ``block_words/``
  （konsheng/Sensitive-lexicon 精选分类，MIT，``l4_block_builtin_words``
  打开才加载）和 ``<data_dir>/block_words/*.txt``（总会加载）。每行一个词，
  ``#`` 开头是注释，少于 2 个字的词不加载，``l4刷新`` 重新读取。

词库匹配前逐字做 NFKC + 小写（全角转半角），长度不变，打码位置能对回原文。
含中文、空格等非字母数字字符的词按子串匹配；纯字母数字的词（xjp、gcd 这类
缩写）按整词匹配，避免 please 误伤 SirPlease 这种英文名。
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from a2s.players import Player
from nonebot.log import logger

from ..config import config

# 包内置词库，``l4_block_builtin_words`` 打开才加载
BUILTIN_WORDS_DIR = Path(__file__).parent.parent / "block_words"
# 少于这么多字的词不加载：单字（死、日……）误伤太多
MIN_WORD_LEN = 2
MASK_CHAR = "*"

_TOKEN_RE = re.compile(r"[a-z0-9]+")


@lru_cache(maxsize=8)
def _compile(patterns: Tuple[str, ...]) -> Tuple[re.Pattern[str], ...]:
    compiled: List[re.Pattern[str]] = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern, re.IGNORECASE))
        except re.error as exc:
            logger.warning(
                f"[l4] l4_block_keywords 里的 {pattern!r} 不是合法正则，已忽略: {exc}",
            )
    return tuple(compiled)


def _patterns() -> Tuple[re.Pattern[str], ...]:
    return _compile(tuple(p for p in config.l4_block_keywords if p))


def _fold(text: str) -> str:
    """逐字 NFKC + 小写；折叠后不是一个字符的字保持原样，保证长度不变。"""
    out: List[str] = []
    for ch in text:
        folded = unicodedata.normalize("NFKC", ch).lower()
        out.append(folded if len(folded) == 1 else ch)
    return "".join(out)


@dataclass(frozen=True)
class _WordSet:
    """词库：按长度分桶做子串查找，几万个词也只是对名字的每个位置查几次集合。"""

    by_len: dict[int, frozenset[str]] = field(default_factory=dict)
    tokens: frozenset[str] = frozenset()

    def __bool__(self) -> bool:
        return bool(self.by_len or self.tokens)

    def spans(self, text: str) -> List[Tuple[int, int]]:
        """``text``（已折叠）里所有命中词的区间。"""
        found: List[Tuple[int, int]] = []
        if self.tokens:
            found += [m.span() for m in _TOKEN_RE.finditer(text) if m[0] in self.tokens]
        for size, bucket in self.by_len.items():
            for i in range(len(text) - size + 1):
                if text[i : i + size] in bucket:
                    found.append((i, i + size))
        return found


def user_words_dir() -> Path:
    """用户词表目录：``<data_dir>/block_words``。"""
    return config.data_dir / "block_words"


def ensure_user_words_dir() -> Path:
    """确保用户词表目录存在（启动时调用，方便找到放词表的位置）。"""
    directory = user_words_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _read_lines(directory: Path) -> List[str]:
    if not directory.is_dir():
        return []
    lines: List[str] = []
    for path in sorted(directory.glob("*.txt")):
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError as exc:
            logger.warning(f"[l4] 读取屏蔽词表 {path} 失败: {exc}")
            continue
        lines.extend(text.splitlines())
    return lines


@lru_cache(maxsize=4)
def _load_words(builtin: bool, user_dir: str) -> _WordSet:
    lines = _read_lines(BUILTIN_WORDS_DIR) if builtin else []
    lines += _read_lines(Path(user_dir))
    by_len: dict[int, set[str]] = {}
    tokens: set[str] = set()
    for line in lines:
        word = _fold(line.strip())
        if len(word) < MIN_WORD_LEN or word.startswith("#"):
            continue
        if word.isascii() and word.isalnum():
            tokens.add(word)
        else:
            by_len.setdefault(len(word), set()).add(word)
    words = _WordSet({n: frozenset(ws) for n, ws in by_len.items()}, frozenset(tokens))
    if words:
        count = len(tokens) + sum(map(len, by_len.values()))
        logger.info(
            f"[l4] 敏感词库已加载 {count} 个词（内置={builtin}，目录 {user_dir}）",
        )
    return words


def _words() -> _WordSet:
    return _load_words(bool(config.l4_block_builtin_words), str(user_words_dir()))


def reload_words() -> None:
    """重新读取词表，下次匹配时生效（重载指令调用）。"""
    _load_words.cache_clear()


def is_blocked(name: str) -> bool:
    """``name`` 命中任意屏蔽关键词（正则）。敏感词库只打码、不屏蔽，见 ``mask``。"""
    return any(p.search(name or "") for p in _patterns())


def mask(text: str) -> str:
    """把敏感词库命中的词替换成 ``*``（等长）；没有词库时原样返回。"""
    words = _words()
    if not text or not words:
        return text
    spans = words.spans(_fold(text))
    if not spans:
        return text
    chars = list(text)
    for start, end in spans:
        chars[start:end] = MASK_CHAR * (end - start)
    return "".join(chars)


def visible_players(players: List[Player]) -> List[Player]:
    """去掉名字命中屏蔽关键词的玩家，其余玩家名里的敏感词替换成 ``*``。

    直接改玩家对象的 ``name``（A2S 每次返回的都是独立拷贝，不会改到缓存）。
    什么都没配置时原样返回。
    """
    if not _patterns() and not _words():
        return players
    shown = [p for p in players if not is_blocked(p.name)]
    for p in shown:
        p.name = mask(p.name)
    return shown
