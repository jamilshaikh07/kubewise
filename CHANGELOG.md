# Changelog

## 1.0.0 (2026-05-15)


### Features

* dark mode toggle + GitHub Actions release workflow ([9542ac7](https://github.com/jamilshaikh07/kubewise/commit/9542ac7433d579cfea99cf3d1a8a5fcc74a3d507))
* exclude system namespaces from collection and recommendations ([82fe8ca](https://github.com/jamilshaikh07/kubewise/commit/82fe8cae290c39ec67af4c49e7953b6bb2093cf6))
* initial KubeWise MVP ([5232983](https://github.com/jamilshaikh07/kubewise/commit/52329831bbe6d9be2ce0b4264d00b546a89561c4))
* update CI to bump ArgoCD app image tags instead of Flux chart version ([360437c](https://github.com/jamilshaikh07/kubewise/commit/360437c13fa4b3a1a5182875a7a4bf6652888dfd))
* version badge in header + release workflow ([0fbba6b](https://github.com/jamilshaikh07/kubewise/commit/0fbba6b2b56e98d2dda70248137493a00d91226f))


### Bug Fixes

* add imagePullSecrets to all Helm pod specs (api, dashboard, agent) ([8402e68](https://github.com/jamilshaikh07/kubewise/commit/8402e688ac9ada9e47699781be9ea60f0bdc3be7))
* address second review pass — 4 remaining issues ([4f60d4c](https://github.com/jamilshaikh07/kubewise/commit/4f60d4cab7443a875cfdedeacdd8cfaac3229db5))
* address senior dev review — all 6 issues ([c7bacf2](https://github.com/jamilshaikh07/kubewise/commit/c7bacf29b0e7b2bef0e6705c387ef2a6fdce46fd))
* disable provenance attestations on GHCR push (403 fix) ([c22ea86](https://github.com/jamilshaikh07/kubewise/commit/c22ea860a34503ebd1ffa8ebd80e18297df46385))
* proxy API via Next.js rewrites so browser uses relative URLs ([9dbf3b5](https://github.com/jamilshaikh07/kubewise/commit/9dbf3b56a360e58ee8f087b98b02e748e120bbe5))
* rewrites baked localhost:8000 at build time from Dockerfile ARG ([b257ae9](https://github.com/jamilshaikh07/kubewise/commit/b257ae9d598c6bab654f7519578f103ab5038917))
* show last synced time in browser local timezone (IST) ([caf342e](https://github.com/jamilshaikh07/kubewise/commit/caf342ef363b6e2a77c0397b206d8ce1dcd89713))
* **tests:** use StaticPool for in-memory SQLite test DB ([1b4f222](https://github.com/jamilshaikh07/kubewise/commit/1b4f222bb3966f4d58ea43078be175afb28aa301))
* update gitops path to live Flux location (k8s/flux/sites/pnl) ([87c342b](https://github.com/jamilshaikh07/kubewise/commit/87c342b987576bda313361d5f9bd99b12bdb3c04))
* use GH_PAT for GHCR login (new package push) ([c398d78](https://github.com/jamilshaikh07/kubewise/commit/c398d78f68f77b15ca548b0227b9d071da02b1fa))
