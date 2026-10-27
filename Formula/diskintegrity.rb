class Diskintegrity < Formula
  desc "Check disk health with surface scans, SMART data, and a PASS/FAIL report"
  homepage "https://github.com/VijitSingh97/diskintegrity"
  url "https://github.com/VijitSingh97/diskintegrity/archive/refs/tags/v0.0.2.tar.gz"
  sha256 "3e994269b88fd056a8f3d495706f184aca66bb28a23266ede5f2bb798b88d890"
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
    assert_match "diskintegrity 0.0.2", shell_output("#{bin}/diskintegrity --version")
    assert_match "Check a disk", shell_output("#{bin}/diskintegrity --help")
    assert_match "not allowed with", shell_output("#{bin}/diskintegrity --fast --write 2>&1", 2)
  end
end
