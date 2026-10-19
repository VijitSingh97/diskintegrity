class Diskintegrity < Formula
  desc "Check macOS disk health with surface scans, SMART data, and a PASS/FAIL report"
  homepage "https://github.com/VijitSingh97/diskintegrity"
  url "https://github.com/VijitSingh97/diskintegrity/archive/refs/tags/v0.0.1.tar.gz"
  sha256 "8b79daca9faa410192269b8cad129624ee381e44339f63b2fe32f7cb9f4db891"
  license "MIT"

  depends_on macos: :sonoma
  depends_on "python@3.13"
  depends_on "smartmontools"

  def install
    inreplace "bin/diskintegrity", "#!/usr/bin/env python3",
              "#!#{formula_opt_bin("python@3.13")}/python3.13"
    bin.install "bin/diskintegrity"
    zsh_completion.install "completions/_diskintegrity"
  end

  test do
    assert_match "diskintegrity 0.0.1", shell_output("#{bin}/diskintegrity --version")
    assert_match "Check a macOS disk", shell_output("#{bin}/diskintegrity --help")
    assert_match "not allowed with", shell_output("#{bin}/diskintegrity --fast --write 2>&1", 2)
  end
end
