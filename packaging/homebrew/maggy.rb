# Homebrew formula for maggy (Maggy).
# Lives in the tap repo agy-pet/homebrew-tap as Formula/maggy.rb;
# scripts/release.sh fills in url/sha256 for each tagged version.
class Maggy < Formula
  desc "Dancing Antigravity logo for the agy statusline"
  homepage "https://agy-pet.github.io/"
  url "https://github.com/agy-pet/maggy/releases/download/v0.8.3/maggy-0.8.3.tar.gz"
  sha256 "de699f9ba21fbb342f7c75f32421e41cb79f1f7f448814947982d03d56294a96"
  license "MIT"
  head "https://github.com/agy-pet/maggy.git", branch: "master"

  depends_on "python@3.13"

  def install
    libexec.install Dir["*.py"], "VERSION", "bin"
    (bin/"maggy").write_env_script libexec/"bin/maggy",
      MAGGY_PYTHON: formula_opt_bin("python@3.13")/"python3.13",
      MAGGY_BIN:    opt_bin/"maggy",
      MAGGY_BREW:   "1"
    bash_completion.install "completions/maggy.bash" => "maggy"
    zsh_completion.install "completions/_maggy"
    fish_completion.install "completions/maggy.fish"
  end

  def caveats
    <<~EOS
      To hook Maggy into agy's statusline, run:
        maggy setup

      Then restart agy (or run /statusline enable inside it).
      More: maggy status · maggy preview working · maggy theme xmas · maggy help
      Before uninstalling, run `maggy uninstall` to remove the statusLine entry.
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/maggy version")
    json = '{"agent_state":"working","model":{"display_name":"Gemini"},"terminal_width":120}'
    assert_match "Gemini", pipe_output("#{bin}/maggy statusline", json)
  end
end
