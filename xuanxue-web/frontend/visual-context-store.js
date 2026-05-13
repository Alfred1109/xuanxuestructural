(function () {
    var MANIFEST_KEY = 'xuanxue_visual_context';
    var DB_NAME = 'xuanxue_visual_context_db';
    var STORE_NAME = 'visual_context';
    var RECORD_KEY = 'current';

    function readManifest() {
        try {
            var raw = window.localStorage.getItem(MANIFEST_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (_error) {
            return null;
        }
    }

    function writeManifest(manifest) {
        try {
            if (!manifest) {
                window.localStorage.removeItem(MANIFEST_KEY);
                return;
            }
            window.localStorage.setItem(MANIFEST_KEY, JSON.stringify(manifest));
        } catch (_error) {}
    }

    function openDatabase() {
        return new Promise(function (resolve, reject) {
            if (!window.indexedDB) {
                reject(new Error('当前浏览器不支持本地图片暂存'));
                return;
            }

            var request = window.indexedDB.open(DB_NAME, 1);
            request.onupgradeneeded = function () {
                var db = request.result;
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    db.createObjectStore(STORE_NAME);
                }
            };
            request.onsuccess = function () {
                resolve(request.result);
            };
            request.onerror = function () {
                reject(request.error || new Error('打开本地图片暂存失败'));
            };
        });
    }

    async function readRecord() {
        var db = await openDatabase();
        return new Promise(function (resolve, reject) {
            var tx = db.transaction(STORE_NAME, 'readonly');
            var store = tx.objectStore(STORE_NAME);
            var request = store.get(RECORD_KEY);

            request.onsuccess = function () {
                resolve(request.result || null);
            };
            request.onerror = function () {
                reject(request.error || new Error('读取本地图片暂存失败'));
            };
        });
    }

    async function writeRecord(record) {
        var db = await openDatabase();
        return new Promise(function (resolve, reject) {
            var tx = db.transaction(STORE_NAME, 'readwrite');
            var store = tx.objectStore(STORE_NAME);
            var request = store.put(record, RECORD_KEY);

            request.onsuccess = function () {
                resolve(record);
            };
            request.onerror = function () {
                reject(request.error || new Error('写入本地图片暂存失败'));
            };
        });
    }

    async function deleteRecord() {
        var db = await openDatabase();
        return new Promise(function (resolve, reject) {
            var tx = db.transaction(STORE_NAME, 'readwrite');
            var store = tx.objectStore(STORE_NAME);
            var request = store.delete(RECORD_KEY);

            request.onsuccess = function () {
                resolve();
            };
            request.onerror = function () {
                reject(request.error || new Error('清除本地图片暂存失败'));
            };
        });
    }

    async function saveDraft(draft) {
        var manifest = {
            version: 2,
            kind: 'draft',
            mode: draft.mode || 'bundle',
            mode_label: draft.mode_label || '多维视觉观察',
            summary: draft.summary || '',
            location: draft.location || '',
            scene_type: draft.scene_type || 'generic',
            image_name: draft.image_name || '',
            disclaimer: draft.disclaimer || '',
            consent_required: !!draft.consent_required,
            items: Array.isArray(draft.items) ? draft.items : [],
            saved_at: draft.saved_at || new Date().toISOString()
        };

        await writeRecord({
            version: 2,
            kind: 'draft',
            mode: draft.mode || 'bundle',
            mode_label: draft.mode_label || '多维视觉观察',
            summary: draft.summary || '',
            location: draft.location || '',
            scene_type: draft.scene_type || 'generic',
            image_name: draft.image_name || '',
            disclaimer: draft.disclaimer || '',
            consent_required: !!draft.consent_required,
            items: Array.isArray(draft.items) ? draft.items : [],
            files: draft.files || {},
            saved_at: manifest.saved_at
        });
        writeManifest(manifest);
        return manifest;
    }

    async function loadDraft() {
        var record = await readRecord();
        if (!record || record.kind !== 'draft') {
            return null;
        }
        return record;
    }

    async function clearAll() {
        writeManifest(null);
        try {
            await deleteRecord();
        } catch (_error) {}
    }

    window.visualContextStore = {
        key: MANIFEST_KEY,
        readManifest: readManifest,
        saveDraft: saveDraft,
        loadDraft: loadDraft,
        clear: clearAll
    };
})();
