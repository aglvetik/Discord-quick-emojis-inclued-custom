from __future__ import annotations

import logging

import discord

from config import AppConfig, ConfigError, ReactionSlot, load_config, save_enabled_state


LOGGER = logging.getLogger("reaction_selfbot")
COMMAND_PREFIX = "!"


class ReactionSelfBot(discord.Client):
    def __init__(self, config: AppConfig) -> None:
        super().__init__(max_messages=1000)
        self.config = config

    async def on_ready(self) -> None:
        LOGGER.info("Logged in as %s (%s)", self.user, getattr(self.user, "id", "unknown"))
        for slot in self.config.slots:
            LOGGER.info(
                "Slot %s | %s | user=%s | role=%s | emoji=%s",
                slot.index,
                slot.status_label,
                slot.user_id or "Not set",
                slot.role_id or "No role filter",
                slot.emoji_display,
            )

    async def on_message(self, message: discord.Message) -> None:
        if self.user is None:
            return

        if message.author.id == self.user.id:
            handled = await self._handle_command(message)
            if handled:
                return

        slot = self._match_slot(message)
        if slot is None:
            return

        emoji = self._resolve_emoji(slot)
        if emoji is None:
            LOGGER.error(
                "Slot %s could not resolve emoji. Set EMOJI_NAME_%s for custom emoji fallback.",
                slot.index,
                slot.index,
            )
            return

        try:
            await message.add_reaction(emoji)
            LOGGER.info(
                "Reacted to message %s from user %s using slot %s with %s",
                message.id,
                message.author.id,
                slot.index,
                slot.emoji_display,
            )
        except discord.HTTPException as exc:
            LOGGER.warning(
                "Failed to add reaction for slot %s on message %s: %s",
                slot.index,
                message.id,
                exc,
            )

    async def _handle_command(self, message: discord.Message) -> bool:
        content = message.content.strip()
        if not content.startswith(COMMAND_PREFIX):
            return False

        parts = content.split()
        command = parts[0].lower()

        if command == "!status":
            await message.channel.send(embed=self._build_status_embed())
            return True

        if command not in {"!able", "!disable"}:
            return False

        if len(parts) != 2 or not parts[1].isdigit():
            await message.channel.send("Usage: `!able <1-5>` or `!disable <1-5>`")
            return True

        slot_number = int(parts[1])
        if slot_number < 1 or slot_number > len(self.config.slots):
            await message.channel.send("Slot number must be between 1 and 5.")
            return True

        slot = self.config.get_slot(slot_number)
        slot.enabled = command == "!able"
        save_enabled_state(self.config, slot_number)

        status_text = "enabled" if slot.enabled else "disabled"
        icon = "✅" if slot.enabled else "❌"
        await message.reply(f"{icon} Slot {slot_number} {status_text}.")
        LOGGER.info("Command %s executed for slot %s", command, slot_number)
        return True

    def _match_slot(self, message: discord.Message) -> ReactionSlot | None:
        for slot in reversed(self.config.slots):
            if not slot.enabled:
                continue
            if not slot.is_configured:
                continue
            if slot.user_id != message.author.id:
                continue
            if slot.role_id is not None and not self._has_role(message, slot.role_id):
                continue
            return slot
        return None

    def _has_role(self, message: discord.Message, role_id: int) -> bool:
        if message.guild is None:
            return False

        roles = getattr(message.author, "roles", None)
        if not roles:
            return False

        return any(role.id == role_id for role in roles)

    def _resolve_emoji(self, slot: ReactionSlot) -> discord.Emoji | str | None:
        if slot.emoji_id is not None:
            emoji = self.get_emoji(slot.emoji_id)
            if emoji is not None:
                return emoji
            if slot.emoji_name:
                return f"<:{slot.emoji_name}:{slot.emoji_id}>"
            return None

        return slot.emoji_name

    def _build_status_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎛️ Reaction Slots Status",
            colour=discord.Colour.blurple(),
        )
        for slot in self.config.slots:
            embed.add_field(
                name=f"Slot {slot.index} {'✅ ENABLED' if slot.enabled else '❌ DISABLED'}",
                value=(
                    f"👤 User: `{slot.user_id or 'Not set'}`\n"
                    f"🎭 Role: `{slot.role_id or 'No role filter'}`\n"
                    f"😀 Emoji: {slot.emoji_display}"
                ),
                inline=False,
            )
        embed.set_footer(text="Use !able <n> or !disable <n> to control slots")
        return embed


def configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        force=True,
    )


def main() -> None:
    try:
        config = load_config()
    except ConfigError as exc:
        configure_logging("INFO")
        LOGGER.error("Configuration error: %s", exc)
        raise SystemExit(1) from exc

    configure_logging(config.log_level)
    LOGGER.info("Starting self-bot with discord.py-self")
    client = ReactionSelfBot(config)
    client.run(config.token, reconnect=True)


if __name__ == "__main__":
    main()
