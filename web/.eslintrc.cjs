module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  rules: {
    // window/globalThis 전역에 커스텀 속성을 추가하지 않도록 강제한다 (모듈 import만 사용).
    'no-restricted-syntax': [
      'error',
      {
        selector:
          "AssignmentExpression[left.type='MemberExpression'][left.object.name='window']",
        message: 'window 전역에 속성을 추가하지 마세요. 모듈 import를 사용하세요.',
      },
      {
        selector:
          "AssignmentExpression[left.type='MemberExpression'][left.object.name='globalThis']",
        message: 'globalThis 전역에 속성을 추가하지 마세요. 모듈 import를 사용하세요.',
      },
    ],
  },
};
