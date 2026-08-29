# Douban adapter strategy

Strategy: COOKIE / browser-backed read  
Contract: visible logged-in web data  
Authentication source: user's live Chrome session  
Replay basis: synthetic fixtures plus isolated registry validation

## Evidence and boundary

The eight commands read ordinary Douban pages that are already visible in
the Chrome session connected through OpenCLI Browser Bridge. They use
visible page structure as the contract and do not call undocumented write
endpoints.

The adapters:

- never ask for, print, export, or persist browser cookies;
- never read a Chrome profile from disk;
- never create, edit, rate, publish, or delete anything on Douban;
- stop with typed login, empty-result, argument, or execution errors;
- do not attempt to bypass verification, risk controls, or access controls.

Automated CI cannot validate a real private account. It therefore replays
small, fully synthetic HTML fixtures and validates the plugin from an
isolated temporary OpenCLI home. An optional manual live smoke test may use
only a dedicated test account and must never upload result bodies, cookies,
or browser traces.
