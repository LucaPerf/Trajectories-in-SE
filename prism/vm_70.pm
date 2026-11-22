dtmc

module chain
  s : [0..75] init 0;
  // init
  [] s=0 -> 0.029126213592233007:(s'=1) + 0.0679611650485437:(s'=2) + 0.04854368932038835:(s'=3) + 0.029126213592233007:(s'=4) + 0.04854368932038835:(s'=5) + 0.14563106796116504:(s'=6) + 0.0679611650485437:(s'=7) + 0.029126213592233007:(s'=8) + 0.029126213592233007:(s'=9) + 0.029126213592233007:(s'=10) + 0.04854368932038835:(s'=11) + 0.029126213592233007:(s'=12) + 0.04854368932038835:(s'=13) + 0.0970873786407767:(s'=14) + 0.029126213592233007:(s'=15) + 0.04854368932038835:(s'=16) + 0.14563106796116504:(s'=17) + 0.029126213592233007:(s'=18);
  // find [PATH: repository root] -type f -name [GLOB: python source files] -exec grep -l [TERM: code search term] [ARG: find placeholder] \;,DISCOVERY_REPO
  [] s=1 -> 1.0:(s'=7);
  // find [PATH: repository root] -type f -name [GLOB: python source files] -exec grep -l [TERM: code search term] [ARG: find placeholder] \;,DISCOVERY_SOURCE
  [] s=2 -> 0.67:(s'=7) + 0.33:(s'=19);
  // find [PATH: repository root] -type f -name [GLOB: python source files] | head [COUNT: line limit],DISCOVERY_REPO
  [] s=3 -> 1.0:(s'=10);
  // find [PATH: repository root] -type f -name [GLOB: python source files] | xargs grep -l [TERM: code search term] 2>/dev/null,DISCOVERY_SOURCE
  [] s=4 -> 1.0:(s'=19);
  // find [PATH: repository root] -type f -name [GLOB: python source files] | xargs grep -l [TERM: code search term] | head [COUNT: line limit],DISCOVERY_REPO
  [] s=5 -> 0.5:(s'=7) + 0.5:(s'=20);
  // find [PATH: repository root] -type f -name [GLOB: python source files] | xargs grep -l [TERM: code search term] | head [COUNT: line limit],DISCOVERY_SOURCE
  [] s=6 -> 0.33:(s'=7) + 0.33:(s'=20) + 0.17:(s'=21) + 0.17:(s'=22);
  // grep -n [TERM: code search term] [PATH: source file],DISCOVERY_SOURCE
  [] s=7 -> 0.2:(s'=19) + 0.05:(s'=20) + 0.3:(s'=23) + 0.05:(s'=26) + 0.1:(s'=27) + 0.1:(s'=29) + 0.05:(s'=30) + 0.05:(s'=40) + 0.05:(s'=71) + 0.05:(s'=75);
  // grep -r [TERM: code search term] [PATH: repository directory] --include=[GLOB: python source files] -l,DISCOVERY_REPO
  [] s=8 -> 1.0:(s'=7);
  // grep -r [TERM: code search term] [PATH: repository directory] --include=[GLOB: python source files] -l,DISCOVERY_SOURCE
  [] s=9 -> 1.0:(s'=24);
  // grep -r [TERM: code search term] [PATH: repository directory] --include=[GLOB: python source files] | head [COUNT: line limit],DISCOVERY_SOURCE
  [] s=10 -> 0.33:(s'=19) + 0.67:(s'=26);
  // grep -r [TERM: code search term] [PATH: repository directory] --include=[GLOB: python source files],DISCOVERY_SOURCE
  [] s=11 -> 0.5:(s'=25) + 0.5:(s'=26);
  // grep -r [TERM: code search term] [PATH: repository directory] --include=[GLOB: python source files],ERROR_NONE
  [] s=12 -> 1.0:(s'=7);
  // grep -r [TERM: code search term] [PATH: repository directory],DISCOVERY_REPO
  [] s=13 -> 1.0:(s'=7);
  // grep -r [TERM: code search term] [PATH: repository directory],DISCOVERY_SOURCE
  [] s=14 -> 0.75:(s'=19) + 0.25:(s'=26);
  // grep -r [TERM: code search term] [PATH: source file] -A [COUNT: context lines] -B [COUNT: context lines],DISCOVERY_SOURCE
  [] s=15 -> 1.0:(s'=27);
  // grep -rn [TERM: code search term] [PATH: repository directory] --include=[GLOB: python source files],DISCOVERY_SOURCE
  [] s=16 -> 0.5:(s'=23) + 0.5:(s'=28);
  // grep -rn [TERM: code search term] [PATH: repository directory],DISCOVERY_SOURCE
  [] s=17 -> 0.49504950495049505:(s'=23) + 0.16831683168316833:(s'=29) + 0.16831683168316833:(s'=30) + 0.16831683168316833:(s'=31);
  // grep -rn [TERM: code search term] [PATH: repository directory],ERROR_SOURCE
  [] s=18 -> 1.0:(s'=29);
  // grep -n -A [COUNT: context lines] [TERM: code search term] [PATH: source file],DISCOVERY_SOURCE
  [] s=19 -> 0.1188118811881188:(s'=19) + 0.0594059405940594:(s'=23) + 0.5841584158415841:(s'=27) + 0.0594059405940594:(s'=32) + 0.0594059405940594:(s'=41) + 0.0594059405940594:(s'=42) + 0.0594059405940594:(s'=63);
  // grep -n [TERM: code search term] [PATH: source file] | head [COUNT: line limit],DISCOVERY_SOURCE
  [] s=20 -> 0.11111111111111112:(s'=7) + 0.11111111111111112:(s'=19) + 0.22222222222222224:(s'=23) + 0.11111111111111112:(s'=26) + 0.11111111111111112:(s'=27) + 0.11111111111111112:(s'=33) + 0.11111111111111112:(s'=39) + 0.11111111111111112:(s'=49);
  // cat [PATH: source file] | head [COUNT: line limit],INFO_SOURCE
  [] s=21 -> 1.0:(s'=7);
  // head -n [COUNT: line limit] [PATH: source file] | grep -n [TERM: code search term],EMPTY_SOURCE
  [] s=22 -> 1.0:(s'=19);
  // sed -n [RANGE: line range] [PATH: source file],DISCOVERY_SOURCE
  [] s=23 -> 0.05:(s'=7) + 0.15:(s'=23) + 0.5:(s'=27) + 0.05:(s'=34) + 0.1:(s'=39) + 0.05:(s'=48) + 0.05:(s'=61) + 0.05:(s'=73);
  // grep -B [COUNT: context lines] -A [COUNT: context lines] [TERM: code search term] [PATH: source file],DISCOVERY_SOURCE
  [] s=24 -> 0.5:(s'=26) + 0.5:(s'=47);
  // cat [PATH: source file] | grep -A [COUNT: context lines] [TERM: code search term],DISCOVERY_SOURCE
  [] s=25 -> 1.0:(s'=7);
  // grep -A [COUNT: context lines] [TERM: code search term] [PATH: source file],DISCOVERY_SOURCE
  [] s=26 -> 0.1:(s'=20) + 0.2:(s'=26) + 0.3:(s'=27) + 0.1:(s'=35) + 0.1:(s'=43) + 0.1:(s'=53) + 0.1:(s'=55);
  // sed -i [EXPR: substitution expression] [PATH: source file],PROGRESS_PATCH
  [] s=27 -> 0.019417475728155338:(s'=19) + 0.019417475728155338:(s'=26) + 0.058252427184466014:(s'=27) + 0.019417475728155338:(s'=29) + 0.038834951456310676:(s'=32) + 0.019417475728155338:(s'=36) + 0.30097087378640774:(s'=39) + 0.07766990291262135:(s'=40) + 0.07766990291262135:(s'=41) + 0.058252427184466014:(s'=45) + 0.019417475728155338:(s'=47) + 0.019417475728155338:(s'=48) + 0.019417475728155338:(s'=50) + 0.019417475728155338:(s'=51) + 0.019417475728155338:(s'=52) + 0.058252427184466014:(s'=53) + 0.019417475728155338:(s'=54) + 0.019417475728155338:(s'=62) + 0.058252427184466014:(s'=64) + 0.058252427184466014:(s'=72);
  // head -n [COUNT: line limit] [PATH: source file] | tail -n [COUNT: line limit],INFO_SOURCE
  [] s=28 -> 1.0:(s'=37);
  // cat -n [PATH: source file] | sed -n [RANGE: line range],DISCOVERY_SOURCE
  [] s=29 -> 0.25510204081632654:(s'=27) + 0.25510204081632654:(s'=29) + 0.12244897959183673:(s'=32) + 0.12244897959183673:(s'=34) + 0.12244897959183673:(s'=39) + 0.12244897959183673:(s'=59);
  // cat [PATH: source file] | head [COUNT: line limit] | tail [COUNT: line limit],DISCOVERY_SOURCE
  [] s=30 -> 1.0:(s'=27);
  // head -n [COUNT: line limit] [PATH: source file] | tail -n [COUNT: line limit],DISCOVERY_SOURCE
  [] s=31 -> 1.0:(s'=38);
  // python3 -c [SCRIPT: edit source file],PROGRESS_PATCH
  [] s=32 -> 0.25:(s'=39) + 0.25:(s'=40) + 0.25:(s'=45) + 0.25:(s'=56);
  // grep -n -A [COUNT: context lines] [TERM: code search term] [PATH: source file] | head [COUNT: line limit],DISCOVERY_SOURCE
  [] s=33 -> 1.0:(s'=27);
  // grep -n [TERM: code search term] [PATH: source file],EMPTY_SOURCE
  [] s=34 -> 0.33333333333333337:(s'=27) + 0.33333333333333337:(s'=59) + 0.33333333333333337:(s'=60);
  // grep -B [COUNT: context lines] -A [COUNT: context lines] [TERM: code search term] [PATH: source file],REPEATED_SOURCE
  [] s=35 -> 0.25:(s'=27) + 0.5:(s'=35) + 0.25:(s'=44);
  // cat [PATH: source file] | grep -A [COUNT: context lines] [TERM: code search term],PROGRESS_PATCH
  [] s=36 -> 1.0:(s'=39);
  // head -n [COUNT: line limit] [PATH: source file] | grep -n [TERM: code search term],DISCOVERY_SOURCE
  [] s=37 -> 1.0:(s'=23);
  // sed -i [EXPR: substitution expression] [PATH: source file],PROGRESS_SOURCE
  [] s=38 -> 1.0:(s'=46);
  // submit_patch [PATCH: fix subclass check],PROGRESS_TEST__success
  [] s=39 -> 1.0:(s'=39);
  // grep -n -A [COUNT: context lines] [TERM: code search term] [PATH: source file],PROGRESS_PATCH
  [] s=40 -> 0.16831683168316833:(s'=34) + 0.6633663366336634:(s'=39) + 0.16831683168316833:(s'=48);
  // python3 << [SCRIPT: edit source file],PROGRESS_PATCH
  [] s=41 -> 0.12244897959183673:(s'=23) + 0.25510204081632654:(s'=39) + 0.25510204081632654:(s'=41) + 0.12244897959183673:(s'=56) + 0.12244897959183673:(s'=69) + 0.12244897959183673:(s'=72);
  // grep -n -B [COUNT: context lines] -A [COUNT: context lines] [TERM: code search term] [PATH: source file],DISCOVERY_SOURCE
  [] s=42 -> 1.0:(s'=27);
  // grep -n -A [COUNT: context lines] [TERM: code search term] [PATH: source file],ERROR_NONE
  [] s=43 -> 1.0:(s'=19);
  // cat [PATH: source file] | head -n [COUNT: line limit] | grep -n [TERM: code search term],EMPTY_SOURCE
  [] s=44 -> 1.0:(s'=27);
  // cat -n [PATH: source file] | sed -n [RANGE: line range],PROGRESS_PATCH
  [] s=45 -> 0.5:(s'=27) + 0.5:(s'=39);
  // grep -n [TERM: code search term] [PATH: source file],PROGRESS_SOURCE
  [] s=46 -> 1.0:(s'=39);
  // sed -n [RANGE: line range] [PATH: source file],INFO_SOURCE
  [] s=47 -> 0.5:(s'=48) + 0.5:(s'=70);
  // sed -n [RANGE: line range] [PATH: source file],REPEATED_SOURCE
  [] s=48 -> 0.1:(s'=7) + 0.2:(s'=20) + 0.2:(s'=27) + 0.3:(s'=39) + 0.1:(s'=41) + 0.1:(s'=62);
  // exec_command grep -n -B [COUNT: context lines] -A [COUNT: context lines] [TERM: code search term] [PATH: source file],ERROR_NONE
  [] s=49 -> 1.0:(s'=20);
  // sed -n [RANGE: line range] [PATH: source file] | grep -A [COUNT: context lines] [TERM: code search term],ERROR_NONE
  [] s=50 -> 1.0:(s'=7);
  // submit_patch [PATCH: fix subclass check],PROGRESS_TEST)__success
  [] s=51 -> 1.0:(s'=51);
  // cat [PATH: source file] | grep -n -A [COUNT: context lines] -B [COUNT: context lines] [TERM: code search term],DISCOVERY_SOURCE
  [] s=52 -> 1.0:(s'=57);
  // grep -A [COUNT: context lines] [TERM: code search term] [PATH: source file],PROGRESS_PATCH
  [] s=53 -> 0.25:(s'=24) + 0.5:(s'=27) + 0.25:(s'=39);
  // grep -rn [TERM: code search term] [PATH: repository directory],EMPTY_SOURCE
  [] s=54 -> 1.0:(s'=48);
  // grep -r [TERM: code search term] [PATH: repository directory] --include=[GLOB: python source files],DISCOVERY_TEST
  [] s=55 -> 1.0:(s'=58);
  // sed -n [RANGE: line range] [PATH: source file],ERROR_SOURCE
  [] s=56 -> 0.5:(s'=23) + 0.5:(s'=27);
  // grep -r [TERM: code search term] [PATH: repository directory],DISCOVERY_TEST
  [] s=57 -> 1.0:(s'=27);
  // python3 -c [SCRIPT: inspect source file],EMPTY_NONE
  [] s=58 -> 1.0:(s'=27);
  // cat -n [PATH: source file] | sed -n [RANGE: line range],REPEATED_SOURCE
  [] s=59 -> 0.5:(s'=27) + 0.5:(s'=39);
  // grep -n [TERM: code search term] [PATH: source file],REPEATED_SOURCE
  [] s=60 -> 1.0:(s'=19);
  // python3 << [SCRIPT: inspect source file],REPEATED_SOURCE
  [] s=61 -> 0.5:(s'=39) + 0.5:(s'=48);
  // cd [PATH: repository root] && python -m pytest [PATH: issue test file] -v 2>&1 | head [COUNT: line limit],ERROR_TEST
  [] s=62 -> 0.5:(s'=65) + 0.5:(s'=74);
  // grep -n [TERM: code search term] [PATH: source file] 2>&1; echo [STRING: exit status],REPEATED_SOURCE
  [] s=63 -> 1.0:(s'=66);
  // sed -n [RANGE: line range] [PATH: source file],PROGRESS_PATCH
  [] s=64 -> 1.0:(s'=48);
  // cd [PATH: repository root] && python [PATH: test runner script] [ARG: issue test module] 2>&1 | tail [COUNT: line limit],ERROR_TEST
  [] s=65 -> 1.0:(s'=67);
  // grep -n -B [COUNT: context lines] -A [COUNT: context lines] [TERM: code search term] [PATH: source file] 2>&1; echo [STRING: exit status],REPEATED_SOURCE
  [] s=66 -> 1.0:(s'=68);
  // submit_patch [PATCH: fix subclass check],PROGRESS_PATCH__success
  [] s=67 -> 1.0:(s'=67);
  // grep -rn [TERM: code search term] [PATH: repository directory],REPEATED_SOURCE
  [] s=68 -> 1.0:(s'=23);
  // cat -n [PATH: source file] | sed -n [RANGE: line range],INFO_SOURCE
  [] s=69 -> 1.0:(s'=20);
  // grep -n [TERM: code search term] [PATH: repository directory],ERROR_SOURCE
  [] s=70 -> 1.0:(s'=35);
  // grep -n [TERM: code search term] [PATH: source file] | tail [COUNT: line limit],DISCOVERY_SOURCE
  [] s=71 -> 1.0:(s'=29);
  // grep -B [COUNT: context lines] -A [COUNT: context lines] [TERM: code search term] [PATH: source file],PROGRESS_PATCH
  [] s=72 -> 0.25:(s'=7) + 0.5:(s'=27) + 0.25:(s'=39);
  // python3 -c [SCRIPT: inspect source file],EMPTY_SOURCE
  [] s=73 -> 1.0:(s'=48);
  // cd [PATH: repository root] && cat [PATH: source file] | sed -n [RANGE: line range],REPEATED_SOURCE
  [] s=74 -> 1.0:(s'=61);
  // cat [PATH: source file] | grep -B [COUNT: context lines] -A [COUNT: context lines] [TERM: code search term],REPEATED_SOURCE
  [] s=75 -> 1.0:(s'=27);
endmodule

label "success" = s=39 | s=51 | s=67;
label "fail" = false;
label "end" = s=39 | s=51 | s=67;

rewards "steps"
  true : 1;
endrewards
