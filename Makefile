.PHONY: test install clean

test:
	uv run python -m vibe_wellness &

install:
	./install.sh

clean:
	rm -rf /tmp/vibe-wellness.lock /tmp/vibe-wellness-interval
