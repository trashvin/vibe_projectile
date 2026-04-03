import pyglet


class SoundPlayer:
    """Simple sound helper using pyglet.media.Player.

    Uses `queue` to enqueue sources and avoids setting `player.source` directly
    (which is a read-only property in newer pyglet versions).
    """

    _players = {}

    @staticmethod
    def play_sound(path, loop=False, repeat=1):
        try:
            source = pyglet.media.load(path, streaming=False)
        except Exception:
            return

        player = pyglet.media.Player()

        if loop:
            # queue once and set loop
            player.queue(source)
            player.loop = True
        else:
            # queue the source `repeat` times so it plays sequentially
            for _ in range(max(1, int(repeat))):
                player.queue(source)

        player.play()
        SoundPlayer._players[path] = player

    @staticmethod
    def stop_sound(path):
        player = SoundPlayer._players.get(path)
        if player:
            try:
                player.pause()
            except Exception:
                pass
            try:
                player.delete()
            except Exception:
                pass
            del SoundPlayer._players[path]
