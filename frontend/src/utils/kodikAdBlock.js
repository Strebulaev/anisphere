// /**
//  * Kodik AdBlocker
//  * Блокирует рекламу в плеере Kodik на уровне клиента
//  * Полная версия с перехватом fetch, XHR, DOM и сообщений плеера
//  */

// (function() {
//     'use strict';
    
//     console.log('🔴 Kodik AdBlock activated');

//     // Список рекламных доменов и паттернов
//     const adPatterns = [
//         'doubleclick',
//         'googlead',
//         'yandex',
//         'adfox',
//         'ad.kodik',
//         'ads.kodik',
//         'banner',
//         'adservice',
//         'adriver',
//         'criteo',
//         'adriver',
//         'advertising',
//         'advert',
//         'ad.' 
//     ];

//     // === 1. Блокировка через перехват fetch ===
//     const originalFetch = window.fetch;
//     window.fetch = function(url, options) {
//         const urlStr = url.toString();
        
//         if (adPatterns.some(pattern => urlStr.includes(pattern))) {
//             console.log('🚫 Ad blocked (fetch):', urlStr);
//             return Promise.reject(new Error('Ad blocked'));
//         }
//         return originalFetch.apply(this, arguments);
//     };

//     // === 2. Блокировка через перехват XMLHttpRequest ===
//     const XHR = XMLHttpRequest;
//     window.XMLHttpRequest = function() {
//         const xhr = new XHR();
//         const originalOpen = xhr.open;

//         xhr.open = function(method, url) {
//             const urlStr = url.toString();

//             if (adPatterns.some(pattern => urlStr.includes(pattern))) {
//                 console.log('🚫 Ad blocked (XHR):', urlStr);
//                 this._isAd = true;
//                 return;
//             }
//             return originalOpen.apply(this, arguments);
//         };

//         return xhr;
//     };

//     // === 3. Наблюдатель за DOM для удаления рекламных элементов ===
//     const observer = new MutationObserver(function(mutations) {
//         mutations.forEach(function(mutation) {
//             mutation.addedNodes.forEach(function(node) {
//                 if (node.nodeType === 1) { // element node
//                     // Блокировка iframe
//                     if (node.tagName === 'IFRAME') {
//                         const src = node.src || '';
//                         if (adPatterns.some(pattern => src.includes(pattern))) {
//                             node.remove();
//                             console.log('🚫 Ad iframe removed');
//                         }
//                     }

//                     // Блокировка script
//                     if (node.tagName === 'SCRIPT') {
//                         const src = node.src || '';
//                         if (adPatterns.some(pattern => src.includes(pattern))) {
//                             node.remove();
//                             console.log('🚫 Ad script removed');
//                         }
//                     }

//                     // Блокировка div с рекламой
//                     if (node.tagName === 'DIV') {
//                         const className = node.className || '';
//                         const id = node.id || '';
//                         const adIndicators = ['ad', 'banner', 'promo', 'sponsor', 'advert'];
                        
//                         if (adIndicators.some(ind => 
//                             className.toLowerCase().includes(ind) || 
//                             id.toLowerCase().includes(ind))) {
//                             node.style.display = 'none';
//                             console.log('🚫 Ad div hidden');
//                         }
//                     }
//                 }
//             });
//         });
//     });

//     // Запускаем наблюдение после загрузки DOM
//     if (document.body) {
//         observer.observe(document.body, {
//             childList: true,
//             subtree: true
//         });
//     } else {
//         document.addEventListener('DOMContentLoaded', function() {
//             observer.observe(document.body, {
//                 childList: true,
//                 subtree: true
//             });
//         });
//     }

//     // === 4. Перехват и фильтрация сообщений от плеера ===
//     const originalPostMessage = window.postMessage;
//     window.postMessage = function(message, targetOrigin, transfer) {
//         // Проверяем, является ли сообщение рекламным событием от Kodik
//         if (message && typeof message === 'object' && 
//             (message.key === 'kodik_player_advert_ended' || 
//              message.key === 'kodik_player_advert_started')) {
//             console.log('🚫 Ad message intercepted and blocked');
//             return; // Блокируем отправку
//         }
//         return originalPostMessage.call(this, message, targetOrigin, transfer);
//     };

//     // === 5. Перехват сообщений (слушатель) ===
//     const adMessageListener = function(event) {
//         if (event.data && typeof event.data === 'object') {
//             if (event.data.key === 'kodik_player_advert_ended' || 
//                 event.data.key === 'kodik_player_advert_started') {
//                 event.stopImmediatePropagation();
//                 console.log('🚫 Ad message listener blocked');
//             }
//         }
//     };

//     window.addEventListener('message', adMessageListener, true);

//     // === 6. Модификация плеера Kodik ===
//     function initKodikBlocker() {
//         // Проверяем наличие плеера каждую секунду
//         const checkInterval = setInterval(function() {
//             // Ищем объект плеера Kodik
//             if (window.kodikPlayer || window.KodikPlayer) {
//                 const player = window.kodikPlayer || window.KodikPlayer;
                
//                 // Переопределяем методы рекламы
//                 if (player.prototype) {
//                     player.prototype.showAd = function() { 
//                         console.log('🚫 Ad method blocked: showAd');
//                         return Promise.resolve(); 
//                     };
//                     player.prototype.loadBanner = function() { 
//                         console.log('🚫 Ad method blocked: loadBanner');
//                         return Promise.resolve(); 
//                     };
//                     player.prototype.initAd = function() { 
//                         console.log('🚫 Ad method blocked: initAd');
//                         return Promise.resolve(); 
//                     };
//                     player.prototype.displayAd = function() { 
//                         console.log('🚫 Ad method blocked: displayAd');
//                         return Promise.resolve(); 
//                     };
//                 }

//                 clearInterval(checkInterval);
//                 console.log('✅ Kodik player methods patched');
//             }

//             // Альтернативный способ через видео элемент
//             const videos = document.querySelectorAll('video');
//             videos.forEach(video => {
//                 // Пытаемся пропустить рекламу
//                 video.addEventListener('timeupdate', function() {
//                     // Если видео короткое (вероятно, реклама)
//                     if (video.duration < 60 && video.currentTime < video.duration - 2) {
//                         console.log('🚫 Skipping short video (possible ad)');
//                         video.currentTime = video.duration - 0.5;
//                     }
//                 });

//                 // Блокируем события рекламы
//                 video.addEventListener('ad-start', (e) => {
//                     e.stopPropagation();
//                     console.log('🚫 Ad start event blocked');
//                 });
//             });
//         }, 1000);
//     }

//     // Запускаем после загрузки страницы
//     window.addEventListener('load', initKodikBlocker);
// })();