export const INFRASTRUCTURE_TYPES = {
  "Trạm điện": { code: "tram_dien", type: "Point", props: ["ampe_ke", "cam_bien_do_nghieng"], color: "#e6194b" },
  "Cột điện": { code: "cot_dien", type: "Point", props: ["cam_bien_do_nghieng"], color: "#3cb44b" },
  "Đường ống điện": { code: "duong_ong_dien", type: "LineString", props: ["voltage"], color: "#ffe119" },
  "Đèn đường": { code: "den_duong", type: "Point", props: ["phan_anh"], color: "#4363d8" },
  "Đèn giao thông": { code: "den_giao_thong", type: "Point", props: ["phan_anh", "thoi_han_bao_tri", "cam_bien_do_nghieng"], color: "#f58231" },
  "Cống thoát nước": { code: "cong_thoat_nuoc", type: "LineString", props: ["muc_nuoc"], color: "#911eb4" },
  "Ống dẫn nước": { code: "ong_dan_nuoc", type: "LineString", props: ["toc_do_nuoc"], color: "#46f0f0" },
  "Trụ chữa cháy": { code: "tru_chua_chay", type: "Point", props: ["cam_bien_ap_suat_nuoc"], color: "#f032e6" },
  "Trạm sạc": { code: "tram_sac", type: "Point", props: ["phan_anh", "cong_dich_vu_du_lieu"], color: "#bcf60c" }
};

export const MAP_STYLE = { height: "100%", width: "100%" };
export const MAP_CENTER = [15.995634, 108.231593];
export const MAP_ZOOM = 13;
export const ZOOM_THRESHOLD = 15;
