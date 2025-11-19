// modules/main.js
// Phase7 진입점: 기존 `app.js`를 모듈 방식으로 초기화하도록 래핑합니다.
// 이 파일은 `index.html`에서 로드되는 새로운 모듈 진입점입니다.

// 기존의 `app.js`는 이미 ES 모듈로 변환되어 있으므로 임포트하면
// 모듈 수준에서 초기화 코드가 실행됩니다.
import '../app.js';

// 추가적으로 향후 통합 로직(초기화 시 순서 보장, health-check 등)을
// 이 파일에 포함할 수 있습니다.
console.debug('[modules/main] loaded');
