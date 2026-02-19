// /////////////////////////////////////////////////////////

// import { useState } from "react";
// import SiteMap from "./components/SiteMap";

// const API_BASE = "http://localhost:8000";

// function App() {
//   const [planNumber, setPlanNumber] = useState("");
//   const [district, setDistrict] = useState("");
//   const [block, setBlock] = useState("");
//   const [layerType, setLayerType] = useState("plan_agri");

//   const [sites, setSites] = useState([]);
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState("");
//   const [responseMeta, setResponseMeta] = useState(null);

//   const [decisions, setDecisions] = useState({});
//   const [submitResult, setSubmitResult] = useState(null);
//   const [submitting, setSubmitting] = useState(false);

//   // NEW: validation states
//   const [validatingSiteId, setValidatingSiteId] = useState(null);
//   const [validationResult, setValidationResult] = useState(null);
//   const [validationError, setValidationError] = useState("");

//   const handleFetchSites = async (e) => {
//     e.preventDefault();

//     if (!planNumber || !district || !block) {
//       setError("Please fill all fields");
//       return;
//     }

//     setError("");
//     setLoading(true);
//     setSites([]);
//     setResponseMeta(null);
//     setDecisions({});
//     setSubmitResult(null);
//     setValidationResult(null);
//     setValidationError("");

//     try {
//       const res = await fetch(`${API_BASE}/api/plan-sites`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({
//           plan_number: planNumber,
//           district,
//           block,
//           layer_type: layerType,
//         }),
//       });

//       const data = await res.json();

//       if (!res.ok) {
//         setError(data.error || "Something went wrong");
//       } else {
//         setSites(data.sites || []);
//         setResponseMeta({
//           plan_number: data.plan_number,
//           district: data.district,
//           block: data.block,
//           layer_type: data.layer_type,
//           layer_name: data.layer_name,
//           site_count: data.site_count,
//         });
//       }
//     } catch (err) {
//       console.error(err);
//       setError("Backend not reachable");
//     } finally {
//       setLoading(false);
//     }
//   };

//   // update decision for a given site (extended with lulc_class + drainage_distance)
//   const updateDecision = (site, field, value) => {
//     setDecisions((prev) => {
//       const prevSite = prev[site.id] || {};
//       const base = {
//         id: site.id,
//         lat: site.lat,
//         lon: site.lon,
//         structure_type: site.structure_type,
//         status: prevSite.status || "",
//         reason: prevSite.reason || "",
//         comments: prevSite.comments || "",
//         lulc_class: prevSite.lulc_class || "",
//         drainage_distance: prevSite.drainage_distance ?? "",
//       };

//       if (field === "status") {
//         base.status = value;
//         if (value === "pass") {
//           // when passing, we only clear error-1 fields
//           base.reason = "";
//           base.comments = "";
//         }
//       } else if (field === "reason") {
//         base.reason = value;
//       } else if (field === "comments") {
//         base.comments = value;
//       } else if (field === "lulc_class") {
//         base.lulc_class = value;
//       } else if (field === "drainage_distance") {
//         base.drainage_distance = value;
//       }

//       return {
//         ...prev,
//         [site.id]: base,
//       };
//     });
//   };

//   const handleSubmitReview = async () => {
//     if (!responseMeta) {
//       setError("Fetch sites first before submitting review.");
//       return;
//     }

//     const allDecisions = Object.values(decisions);
//     if (allDecisions.length === 0) {
//       setError("You have not marked any site as Pass or Flag.");
//       return;
//     }

//     setError("");
//     setSubmitting(true);
//     setSubmitResult(null);

//     try {
//       const res = await fetch(`${API_BASE}/api/error1/submit`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({
//           plan_number: responseMeta.plan_number,
//           district: responseMeta.district,
//           block: responseMeta.block,
//           layer_type: responseMeta.layer_type,
//           decisions: allDecisions,
//         }),
//       });

//       const data = await res.json();

//       if (!res.ok) {
//         setError(data.error || "Failed to submit Error 1 review");
//       } else {
//         setSubmitResult(data);
//       }
//     } catch (err) {
//       console.error(err);
//       setError("Backend not reachable during submit");
//     } finally {
//       setSubmitting(false);
//     }
//   };

//   // ---------- VALIDATION (Error 3-ish) ----------

//   const handleValidateSite = async (site) => {
//     setValidationError("");
//     setValidationResult(null);
//     setValidatingSiteId(site.id);

//     const dec = decisions[site.id] || {};
//     // For now manual entry; later we hook LULC + drainage from rasters
//     const lulc = dec.lulc_class || "Croplands";
//     const drainage =
//       dec.drainage_distance !== "" && dec.drainage_distance !== undefined
//         ? Number(dec.drainage_distance)
//         : 80;

//     try {
//       const payload = {
//         lat: site.lat,
//         lon: site.lon,
//         structure_type: site.structure_type || "Check dam",
//         lulc_class: lulc,
//         drainage_distance: drainage,
//       };

//       const res = await fetch(`${API_BASE}/api/validate-site`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify(payload),
//       });

//       const data = await res.json();
//       if (!res.ok) {
//         throw new Error(data.error || "Validation failed");
//       }

//       setValidationResult({
//         siteId: site.id,
//         siteLabel: `${site.structure_type || ""} @ (${site.lat.toFixed(
//           5
//         )}, ${site.lon.toFixed(5)})`,
//         data,
//       });
//     } catch (err) {
//       console.error(err);
//       setValidationError(err.message || "Failed to validate site");
//     } finally {
//       setValidatingSiteId(null);
//     }
//   };

//   const totalSites = sites.length;
//   const decided = Object.values(decisions).filter(
//     (d) => d.status === "pass" || d.status === "flag"
//   ).length;
//   const flaggedLocal = Object.values(decisions).filter(
//     (d) => d.status === "flag"
//   ).length;

//   // badge color helper for validation report
//   const badgeColor = (category) => {
//     switch (category) {
//       case "accepted":
//       case "valid":
//         return "bg-emerald-500/20 text-emerald-200 border-emerald-400";
//       case "partially_accepted":
//       case "be_careful":
//         return "bg-amber-500/20 text-amber-200 border-amber-400";
//       case "not_accepted":
//         return "bg-rose-500/20 text-rose-200 border-rose-400";
//       case "not_evaluated":
//       default:
//         return "bg-slate-700 text-slate-200 border-slate-500";
//     }
//   };

//   return (
//     <div className="min-h-screen bg-slate-950 text-white p-8">
//       <h1 className="text-3xl font-bold mb-6">
//         Plan Site Extraction & Error 1 Review
//       </h1>

//       {/* Input Form */}
//       <div className="bg-slate-900 border border-slate-700 p-6 rounded-xl max-w-xl mb-8">
//         <form onSubmit={handleFetchSites}>
//           <label className="block text-sm mb-1">Plan Number</label>
//           <input
//             className="w-full p-2 rounded bg-slate-800 mb-3"
//             placeholder="116"
//             value={planNumber}
//             onChange={(e) => setPlanNumber(e.target.value)}
//           />

//           <label className="block text-sm mb-1">District</label>
//           <input
//             className="w-full p-2 rounded bg-slate-800 mb-3"
//             placeholder="bhilwara"
//             value={district}
//             onChange={(e) => setDistrict(e.target.value)}
//           />

//           <label className="block text-sm mb-1">Block</label>
//           <input
//             className="w-full p-2 rounded bg-slate-800 mb-3"
//             placeholder="mandalgarh"
//             value={block}
//             onChange={(e) => setBlock(e.target.value)}
//           />

//           <label className="block text-sm mb-1">Layer Type</label>
//           <select
//             className="w-full p-2 rounded bg-slate-800 mb-4"
//             value={layerType}
//             onChange={(e) => setLayerType(e.target.value)}
//           >
//             <option value="plan_agri">Agriculture (plan_agri)</option>
//             <option value="plan_gw">Groundwater (plan_gw)</option>
//             <option value="waterbody">Waterbody (resources)</option>
//           </select>

//           {error && <p className="text-red-400 mb-3">{error}</p>}

//           <button
//             type="submit"
//             className="bg-green-500 text-black px-4 py-2 rounded-full font-semibold"
//           >
//             {loading ? "Fetching..." : "Extract Sites"}
//           </button>
//         </form>
//       </div>

//       {/* Response Summary */}
//       {responseMeta && (
//         <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl max-w-2xl mb-6 text-sm">
//           <p>
//             <b>Layer:</b> {responseMeta.layer_name}
//           </p>
//           <p>
//             <b>Total Sites:</b> {responseMeta.site_count}
//           </p>
//           <p>
//             <b>Location:</b> {responseMeta.district} / {responseMeta.block}
//           </p>
//           <p className="mt-2 text-slate-300 text-xs">
//             Please use the satellite view on the right to visually check each
//             point before marking Pass or Flag. Validation uses GEE for slope,
//             catchment and stream order for sites marked <b>Pass</b>.
//           </p>
//         </div>
//       )}

//       {/* Table + Map + Validation */}
//       {sites.length > 0 && (
//         <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-6xl">
//           {/* Table with decisions & validate */}
//           <div className="bg-slate-900 border border-slate-700 p-6 rounded-xl overflow-x-auto">
//             <h2 className="text-xl font-semibold mb-2">Extracted Sites</h2>
//             <p className="text-xs text-slate-300 mb-4">
//               1) Use map to review coordinates. 2) Mark{" "}
//               <span className="text-green-400">Pass</span> /
//               <span className="text-red-400">Flag</span>. 3) For passed sites,
//               enter LULC & drainage (temporary manual) and click{" "}
//               <span className="font-semibold">Validate</span>.
//             </p>

//             <table className="w-full text-xs border-collapse">
//               <thead>
//                 <tr className="border-b border-slate-700">
//                   <th className="py-2 text-left">Structure</th>
//                   <th className="py-2 text-left">Lat</th>
//                   <th className="py-2 text-left">Lon</th>
//                   <th className="py-2 text-left">Decision</th>
//                   <th className="py-2 text-left">Reason (if Flag)</th>
//                   <th className="py-2 text-left">Comments</th>
//                   <th className="py-2 text-left">LULC</th>
//                   <th className="py-2 text-left">Drain (m)</th>
//                   <th className="py-2 text-left">Validate</th>
//                 </tr>
//               </thead>
//               <tbody>
//                 {sites.map((site) => {
//                   const dec = decisions[site.id] || {};
//                   const isPass = dec.status === "pass";

//                   return (
//                     <tr
//                       key={site.id}
//                       className="border-b border-slate-800 align-top"
//                     >
//                       <td className="py-2 pr-2">
//                         <div className="font-semibold">
//                           {site.structure_type || "-"}
//                         </div>
//                         <div className="text-[10px] text-slate-400 break-all">
//                           {site.id}
//                         </div>
//                       </td>
//                       <td className="py-2 pr-2">{site.lat}</td>
//                       <td className="py-2 pr-2">{site.lon}</td>
//                       <td className="py-2 pr-2">
//                         <div className="flex gap-2">
//                           <button
//                             type="button"
//                             className={`px-2 py-1 rounded-full text-xs ${
//                               dec.status === "pass"
//                                 ? "bg-green-500 text-black"
//                                 : "bg-slate-800"
//                             }`}
//                             onClick={() =>
//                               updateDecision(site, "status", "pass")
//                             }
//                           >
//                             Pass
//                           </button>
//                           <button
//                             type="button"
//                             className={`px-2 py-1 rounded-full text-xs ${
//                               dec.status === "flag"
//                                 ? "bg-red-500 text-black"
//                                 : "bg-slate-800"
//                             }`}
//                             onClick={() =>
//                               updateDecision(site, "status", "flag")
//                             }
//                           >
//                             Flag
//                           </button>
//                         </div>
//                       </td>
//                       <td className="py-2 pr-2">
//                         {dec.status === "flag" && (
//                           <select
//                             className="bg-slate-800 px-2 py-1 rounded w-40"
//                             value={dec.reason || ""}
//                             onChange={(e) =>
//                               updateDecision(site, "reason", e.target.value)
//                             }
//                           >
//                             <option value="">Select reason</option>
//                             <option value="mis_marking">
//                               Mis-marking (structure at distance)
//                             </option>
//                             <option value="built_up">Built-up area</option>
//                             <option value="inside_water">
//                               Inside waterbody
//                             </option>
//                             <option value="no_structure">
//                               No visible structure
//                             </option>
//                             <option value="other">Other</option>
//                           </select>
//                         )}
//                       </td>
//                       <td className="py-2 pr-2">
//                         {dec.status === "flag" && (
//                           <input
//                             className="bg-slate-800 px-2 py-1 rounded w-40"
//                             placeholder="Optional notes"
//                             value={dec.comments || ""}
//                             onChange={(e) =>
//                               updateDecision(site, "comments", e.target.value)
//                             }
//                           />
//                         )}
//                       </td>

//                       {/* LULC manual */}
//                       <td className="py-2 pr-2">
//                         {isPass && (
//                           <input
//                             className="bg-slate-800 px-2 py-1 rounded w-32"
//                             placeholder="Croplands"
//                             value={dec.lulc_class || ""}
//                             onChange={(e) =>
//                               updateDecision(site, "lulc_class", e.target.value)
//                             }
//                           />
//                         )}
//                       </td>

//                       {/* Drainage distance manual */}
//                       <td className="py-2 pr-2">
//                         {isPass && (
//                           <input
//                             type="number"
//                             className="bg-slate-800 px-2 py-1 rounded w-24"
//                             placeholder="80"
//                             value={
//                               dec.drainage_distance !== undefined
//                                 ? dec.drainage_distance
//                                 : ""
//                             }
//                             onChange={(e) =>
//                               updateDecision(
//                                 site,
//                                 "drainage_distance",
//                                 e.target.value
//                               )
//                             }
//                           />
//                         )}
//                       </td>

//                       {/* Validate button */}
//                       <td className="py-2 pr-2">
//                         <button
//                           type="button"
//                           disabled={!isPass || validatingSiteId === site.id}
//                           onClick={() => handleValidateSite(site)}
//                           className={`px-3 py-1 rounded-full text-xs border ${
//                             !isPass || validatingSiteId === site.id
//                               ? "border-slate-600 text-slate-500"
//                               : "border-indigo-400 text-indigo-200 hover:bg-indigo-500/10"
//                           }`}
//                         >
//                           {validatingSiteId === site.id
//                             ? "Validating..."
//                             : "Validate"}
//                         </button>
//                       </td>
//                     </tr>
//                   );
//                 })}
//               </tbody>
//             </table>

//             {/* Decision summary and submit */}
//             <div className="mt-4 flex flex-col gap-2 text-xs text-slate-300">
//               <div>
//                 Decided: {decided}/{totalSites} | Flagged: {flaggedLocal}
//               </div>
//               <button
//                 type="button"
//                 onClick={handleSubmitReview}
//                 className="mt-1 bg-blue-500 text-black px-4 py-2 rounded-full font-semibold max-w-xs"
//               >
//                 {submitting ? "Submitting..." : "Submit Error 1 Review"}
//               </button>
//               {submitResult && (
//                 <div className="mt-2 text-green-400">
//                   Saved flagged sites: {submitResult.flagged_count} | Passed
//                   sites: {submitResult.passed_count}
//                 </div>
//               )}
//             </div>
//           </div>

//           {/* Map + Validation panel */}
//           <div className="flex flex-col gap-4">
//             <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl">
//               <h2 className="text-xl font-semibold mb-4">Satellite View</h2>
//               <SiteMap sites={sites} />
//             </div>

//             <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl text-xs">
//               <h2 className="text-sm font-semibold mb-2">
//                 Rule-based Validation Report
//               </h2>

//               {!validationResult && !validationError && (
//                 <p className="text-slate-300">
//                   Select a site marked{" "}
//                   <span className="text-green-400 font-semibold">Pass</span> and
//                   click <span className="font-semibold">Validate</span> to see
//                   GEE + rules.json evaluation here.
//                 </p>
//               )}

//               {validationError && (
//                 <div className="mt-2 rounded border border-rose-500/60 bg-rose-900/20 px-3 py-2 text-rose-200">
//                   {validationError}
//                 </div>
//               )}

//               {validationResult && (
//                 <ValidationDetail
//                   result={validationResult.data}
//                   siteLabel={validationResult.siteLabel}
//                   badgeColor={badgeColor}
//                 />
//               )}
//             </div>
//           </div>
//         </div>
//       )}
//     </div>
//   );
// }

// /* ---------- Validation detail components ---------- */

// function ValidationDetail({ result, siteLabel, badgeColor }) {
//   const params = result.evaluation?.parameters;
//   const raw = result.raw_values || {};

//   return (
//     <div className="mt-2 space-y-3">
//       <p className="text-[11px] text-slate-300">
//         Site: <span className="font-semibold">{siteLabel}</span>
//       </p>

//       <div>
//         <h3 className="font-semibold text-slate-100 mb-1 text-xs">
//           Raw values (from GEE + inputs)
//         </h3>
//         <div className="grid gap-1 md:grid-cols-2 text-[11px]">
//           <p>
//             <span className="font-medium text-slate-200">
//               Slope mean (30m):
//             </span>{" "}
//             {raw.slope_mean_30m} %
//           </p>
//           <p>
//             <span className="font-medium text-slate-200">
//               Catchment min (30m):
//             </span>{" "}
//             {raw.catchment_min_30m} ha
//           </p>
//           <p>
//             <span className="font-medium text-slate-200">
//               Catchment max (30m):
//             </span>{" "}
//             {raw.catchment_max_30m} ha
//           </p>
//           <p>
//             <span className="font-medium text-slate-200">Stream order:</span>{" "}
//             {raw.stream_order}
//           </p>
//           <p>
//             <span className="font-medium text-slate-200">
//               Drainage distance:
//             </span>{" "}
//             {raw.drainage_distance ?? "—"} m
//           </p>
//           <p>
//             <span className="font-medium text-slate-200">LULC:</span>{" "}
//             {raw.lulc_class || "—"}
//           </p>
//         </div>
//       </div>

//       <div className="space-y-2">
//         <ParamBlock
//           title="Slope"
//           param={params?.slope}
//           badgeColor={badgeColor}
//         />
//         <ParamBlock
//           title="Catchment Area"
//           param={params?.catchment_area}
//           badgeColor={badgeColor}
//         />
//         <ParamBlock
//           title="Stream Order"
//           param={params?.stream_order}
//           badgeColor={badgeColor}
//         />
//         <ParamBlock
//           title="Drainage Distance"
//           param={params?.drainage_distance}
//           badgeColor={badgeColor}
//         />
//         <ParamBlock title="LULC" param={params?.lulc} badgeColor={badgeColor} />
//       </div>

//       <p className="text-[11px] text-slate-400">
//         {result.evaluation?.overall_comment}
//       </p>
//     </div>
//   );
// }

// function ParamBlock({ title, param, badgeColor }) {
//   if (!param) return null;
//   return (
//     <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-2">
//       <div className="flex items-center justify-between mb-1">
//         <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-300">
//           {title}
//         </span>
//         <span
//           className={
//             "px-2 py-0.5 rounded-full border text-[11px] font-medium " +
//             badgeColor(param.category)
//           }
//         >
//           {param.category}
//         </span>
//       </div>
//       <p className="text-[11px] text-slate-200">{param.explanation}</p>
//     </div>
//   );
// }

// export default App;








///////////////////////////////////////////////////////////////////////////////////////////////

// part 2: the valid part without lulc integration 

// import { useState, useEffect, useMemo } from "react";
// import SiteMap from "./components/SiteMap";

// const API_BASE = "http://localhost:8000";

// const PROPOSED_BLOCKS_API =
//   "https://geoserver.core-stack.org/api/v1/proposed_blocks/";

// function PlanSelector({ onSelectionChange }) {
//   const [states, setStates] = useState([]);
//   const [loading, setLoading] = useState(false);
//   const [err, setErr] = useState("");

//   const [selectedStateId, setSelectedStateId] = useState("");
//   const [selectedDistrictId, setSelectedDistrictId] = useState("");
//   const [selectedBlockId, setSelectedBlockId] = useState("");

//   // Fetch once
//   useEffect(() => {
//     const fetchData = async () => {
//       setLoading(true);
//       setErr("");
//       try {
//         const res = await fetch(PROPOSED_BLOCKS_API);
//         if (!res.ok) throw new Error(`API error: ${res.status}`);
//         const data = await res.json();
//         // data is: [ { label, state_id, district: [ ... ] }, ... ]
//         setStates(Array.isArray(data) ? data : []);
//       } catch (e) {
//         console.error(e);
//         setErr("Failed to load state/district/block list.");
//       } finally {
//         setLoading(false);
//       }
//     };
//     fetchData();
//   }, []);

//   // Find selected objects
//   const selectedState = useMemo(
//     () => states.find((s) => s.state_id === selectedStateId) || null,
//     [states, selectedStateId]
//   );

//   const districtOptions = useMemo(
//     () => (selectedState ? selectedState.district || [] : []),
//     [selectedState]
//   );

//   const selectedDistrict = useMemo(
//     () =>
//       districtOptions.find((d) => d.district_id === selectedDistrictId) || null,
//     [districtOptions, selectedDistrictId]
//   );

//   const blockOptions = useMemo(
//     () => (selectedDistrict ? selectedDistrict.blocks || [] : []),
//     [selectedDistrict]
//   );

//   const selectedBlock = useMemo(
//     () => blockOptions.find((b) => b.block_id === selectedBlockId) || null,
//     [blockOptions, selectedBlockId]
//   );

//   // Push selection to parent whenever it changes
//   useEffect(() => {
//     if (!onSelectionChange) return;
//     onSelectionChange({
//       stateLabel: selectedState?.label || "",
//       stateId: selectedState?.state_id || "",
//       districtLabel: selectedDistrict?.label || "",
//       districtId: selectedDistrict?.district_id || "",
//       blockLabel: selectedBlock?.label || "",
//       blockId: selectedBlock?.block_id || "",
//     });
//   }, [selectedState, selectedDistrict, selectedBlock, onSelectionChange]);

//   // Handlers
//   const handleStateChange = (e) => {
//     const v = e.target.value;
//     setSelectedStateId(v);
//     setSelectedDistrictId("");
//     setSelectedBlockId("");
//   };

//   const handleDistrictChange = (e) => {
//     const v = e.target.value;
//     setSelectedDistrictId(v);
//     setSelectedBlockId("");
//   };

//   const handleBlockChange = (e) => {
//     const v = e.target.value;
//     setSelectedBlockId(v);
//   };

//   return (
//     <div className="space-y-2">
//       {loading && (
//         <p className="text-xs text-slate-400">Loading locations...</p>
//       )}
//       {err && <p className="text-xs text-red-400">{err}</p>}

//       {/* State */}
//       <div>
//         <label className="block text-sm mb-1">State</label>
//         <select
//           className="w-full p-2 rounded bg-slate-800"
//           value={selectedStateId}
//           onChange={handleStateChange}
//         >
//           <option value="">Select state</option>
//           {states.map((s) => (
//             <option key={s.state_id} value={s.state_id}>
//               {s.label}
//             </option>
//           ))}
//         </select>
//       </div>

//       {/* District */}
//       <div>
//         <label className="block text-sm mb-1">District</label>
//         <select
//           className="w-full p-2 rounded bg-slate-800"
//           value={selectedDistrictId}
//           onChange={handleDistrictChange}
//           disabled={!selectedStateId}
//         >
//           <option value="">Select district</option>
//           {districtOptions.map((d) => (
//             <option key={d.district_id} value={d.district_id}>
//               {d.label}
//             </option>
//           ))}
//         </select>
//       </div>

//       {/* Block */}
//       <div>
//         <label className="block text-sm mb-1">Block</label>
//         <select
//           className="w-full p-2 rounded bg-slate-800"
//           value={selectedBlockId}
//           onChange={handleBlockChange}
//           disabled={!selectedDistrictId}
//         >
//           <option value="">Select block</option>
//           {blockOptions.map((b) => (
//             <option key={b.block_id} value={b.block_id}>
//               {b.label}
//             </option>
//           ))}
//         </select>
//       </div>
//     </div>
//   );
// }


// function App() {
//   const [planNumber, setPlanNumber] = useState("");
//   const [district, setDistrict] = useState("");
//   const [block, setBlock] = useState("");
//   const [layerType, setLayerType] = useState("plan_agri");

//   const [sites, setSites] = useState([]);
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState("");
//   const [responseMeta, setResponseMeta] = useState(null);

//   const [decisions, setDecisions] = useState({});
//   const [submitResult, setSubmitResult] = useState(null);
//   const [submitting, setSubmitting] = useState(false);

//   // NEW: validation states
//   const [validatingSiteId, setValidatingSiteId] = useState(null);
//   const [validationResult, setValidationResult] = useState(null);
//   const [validationError, setValidationError] = useState("");

//   const handleFetchSites = async (e) => {
//     e.preventDefault();

//     if (!planNumber || !district || !block) {
//       setError("Please fill all fields");
//       return;
//     }

//     setError("");
//     setLoading(true);
//     setSites([]);
//     setResponseMeta(null);
//     setDecisions({});
//     setSubmitResult(null);
//     setValidationResult(null);
//     setValidationError("");

//     try {
//       const res = await fetch(`${API_BASE}/api/plan-sites`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({
//           plan_number: planNumber,
//           district,
//           block,
//           layer_type: layerType,
//         }),
//       });

//       const data = await res.json();

//       if (!res.ok) {
//         setError(data.error || "Something went wrong");
//       } else {
//         setSites(data.sites || []);
//         setResponseMeta({
//           plan_number: data.plan_number,
//           district: data.district,
//           block: data.block,
//           layer_type: data.layer_type,
//           layer_name: data.layer_name,
//           site_count: data.site_count,
//         });
//       }
//     } catch (err) {
//       console.error(err);
//       setError("Backend not reachable");
//     } finally {
//       setLoading(false);
//     }
//   };

//   // update decision for a given site (extended with lulc_class + drainage_distance)
//   const updateDecision = (site, field, value) => {
//     setDecisions((prev) => {
//       const prevSite = prev[site.id] || {};
//       const base = {
//         id: site.id,
//         lat: site.lat,
//         lon: site.lon,
//         structure_type: site.structure_type,
//         status: prevSite.status || "",
//         reason: prevSite.reason || "",
//         comments: prevSite.comments || "",
//         lulc_class: prevSite.lulc_class || "",
//         drainage_distance: prevSite.drainage_distance ?? "",
//       };

//       if (field === "status") {
//         base.status = value;
//         if (value === "pass") {
//           // when passing, we only clear error-1 fields
//           base.reason = "";
//           base.comments = "";
//         }
//       } else if (field === "reason") {
//         base.reason = value;
//       } else if (field === "comments") {
//         base.comments = value;
//       } else if (field === "lulc_class") {
//         base.lulc_class = value;
//       } else if (field === "drainage_distance") {
//         base.drainage_distance = value;
//       }

//       return {
//         ...prev,
//         [site.id]: base,
//       };
//     });
//   };

//   const handleSubmitReview = async () => {
//     if (!responseMeta) {
//       setError("Fetch sites first before submitting review.");
//       return;
//     }

//     const allDecisions = Object.values(decisions);
//     if (allDecisions.length === 0) {
//       setError("You have not marked any site as Pass or Flag.");
//       return;
//     }

//     setError("");
//     setSubmitting(true);
//     setSubmitResult(null);

//     try {
//       const res = await fetch(`${API_BASE}/api/error1/submit`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({
//           plan_number: responseMeta.plan_number,
//           district: responseMeta.district,
//           block: responseMeta.block,
//           layer_type: responseMeta.layer_type,
//           decisions: allDecisions,
//         }),
//       });

//       const data = await res.json();

//       if (!res.ok) {
//         setError(data.error || "Failed to submit Error 1 review");
//       } else {
//         setSubmitResult(data);
//       }
//     } catch (err) {
//       console.error(err);
//       setError("Backend not reachable during submit");
//     } finally {
//       setSubmitting(false);
//     }
//   };

//   // ---------- VALIDATION (Error 3-ish) ----------

//   const handleValidateSite = async (site) => {
//     setValidationError("");
//     setValidationResult(null);
//     setValidatingSiteId(site.id);

//     const dec = decisions[site.id] || {};
//     // For now manual entry; later we hook LULC + drainage from rasters
//     const lulc = dec.lulc_class || "Croplands";
//     const drainage =
//       dec.drainage_distance !== "" && dec.drainage_distance !== undefined
//         ? Number(dec.drainage_distance)
//         : 80;

//     try {
//       const payload = {
//         lat: site.lat,
//         lon: site.lon,
//         structure_type: site.structure_type || "Check dam",
//         lulc_class: lulc,
//         drainage_distance: drainage,
//       };

//       const res = await fetch(`${API_BASE}/api/validate-site`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify(payload),
//       });

//       const data = await res.json();
//       if (!res.ok) {
//         throw new Error(data.error || "Validation failed");
//       }

//       setValidationResult({
//         siteId: site.id,
//         siteLabel: `${site.structure_type || ""} @ (${site.lat.toFixed(
//           5
//         )}, ${site.lon.toFixed(5)})`,
//         data,
//       });
//     } catch (err) {
//       console.error(err);
//       setValidationError(err.message || "Failed to validate site");
//     } finally {
//       setValidatingSiteId(null);
//     }
//   };

//   const totalSites = sites.length;
//   const decided = Object.values(decisions).filter(
//     (d) => d.status === "pass" || d.status === "flag"
//   ).length;
//   const flaggedLocal = Object.values(decisions).filter(
//     (d) => d.status === "flag"
//   ).length;

//   // badge color helper for validation report
//   const badgeColor = (category) => {
//     switch (category) {
//       case "accepted":
//       case "valid":
//         return "bg-emerald-500/20 text-emerald-200 border-emerald-400";
//       case "partially_accepted":
//       case "be_careful":
//         return "bg-amber-500/20 text-amber-200 border-amber-400";
//       case "not_accepted":
//         return "bg-rose-500/20 text-rose-200 border-rose-400";
//       case "not_evaluated":
//       default:
//         return "bg-slate-700 text-slate-200 border-slate-500";
//     }
//   };

//   return (
//     <div className="min-h-screen bg-slate-950 text-white p-8">
//       <h1 className="text-3xl font-bold mb-6">
//         Plan Site Extraction & Error 1 Review
//       </h1>

//       {/* Input Form */}
//       <div className="bg-slate-900 border border-slate-700 p-6 rounded-xl max-w-xl mb-8">
//         <form onSubmit={handleFetchSites}>
//           {/* NEW: cascading State → District → Block */}
//           <PlanSelector
//            onSelectionChange={({ districtLabel, blockLabel }) => {
//               setDistrict(districtLabel ? districtLabel.toLowerCase() : "");
//               setBlock(blockLabel ? blockLabel.toLowerCase() : "");
//             }}

//           />

//           {/* Plan number still manual for now */}
//           <label className="block text-sm mb-1 mt-4">Plan Number</label>
//           <input
//             className="w-full p-2 rounded bg-slate-800 mb-3"
//             placeholder="116"
//             value={planNumber}
//             onChange={(e) => setPlanNumber(e.target.value)}
//           />

//           <label className="block text-sm mb-1">Layer Type</label>
//           <select
//             className="w-full p-2 rounded bg-slate-800 mb-4"
//             value={layerType}
//             onChange={(e) => setLayerType(e.target.value)}
//           >
//             <option value="plan_agri">Agriculture (plan_agri)</option>
//             <option value="plan_gw">Groundwater (plan_gw)</option>
//             <option value="waterbody">Waterbody (resources)</option>
//           </select>

//           {error && <p className="text-red-400 mb-3">{error}</p>}

//           <button
//             type="submit"
//             className="bg-green-500 text-black px-4 py-2 rounded-full font-semibold"
//           >
//             {loading ? "Fetching..." : "Extract Sites"}
//           </button>

//           <p className="mt-2 text-[11px] text-slate-400">
//             Selected district/block: {district || "—"} / {block || "—"}
//           </p>
//         </form>
//       </div>

//       {/* Response Summary */}
//       {responseMeta && (
//         <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl max-w-2xl mb-6 text-sm">
//           <p>
//             <b>Layer:</b> {responseMeta.layer_name}
//           </p>
//           <p>
//             <b>Total Sites:</b> {responseMeta.site_count}
//           </p>
//           <p>
//             <b>Location:</b> {responseMeta.district} / {responseMeta.block}
//           </p>
//           <p className="mt-2 text-slate-300 text-xs">
//             Please use the satellite view on the right to visually check each
//             point before marking Pass or Flag. Validation uses GEE for slope,
//             catchment and stream order for sites marked <b>Pass</b>.
//           </p>
//         </div>
//       )}

//       {/* Table + Map + Validation */}
//       {sites.length > 0 && (
//         <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-6xl">
//           {/* Table with decisions & validate */}
//           <div className="bg-slate-900 border border-slate-700 p-6 rounded-xl overflow-x-auto">
//             <h2 className="text-xl font-semibold mb-2">Extracted Sites</h2>
//             <p className="text-xs text-slate-300 mb-4">
//               1) Use map to review coordinates. 2) Mark{" "}
//               <span className="text-green-400">Pass</span> /
//               <span className="text-red-400">Flag</span>. 3) For passed sites,
//               enter LULC & drainage (temporary manual) and click{" "}
//               <span className="font-semibold">Validate</span>.
//             </p>

//             <table className="w-full text-xs border-collapse">
//               <thead>
//                 <tr className="border-b border-slate-700">
//                   <th className="py-2 text-left">Structure</th>
//                   <th className="py-2 text-left">Lat</th>
//                   <th className="py-2 text-left">Lon</th>
//                   <th className="py-2 text-left">Decision</th>
//                   <th className="py-2 text-left">Reason (if Flag)</th>
//                   <th className="py-2 text-left">Comments</th>
//                   <th className="py-2 text-left">LULC</th>
//                   <th className="py-2 text-left">Drain (m)</th>
//                   <th className="py-2 text-left">Validate</th>
//                 </tr>
//               </thead>
//               <tbody>
//                 {sites.map((site) => {
//                   const dec = decisions[site.id] || {};
//                   const isPass = dec.status === "pass";

//                   return (
//                     <tr
//                       key={site.id}
//                       className="border-b border-slate-800 align-top"
//                     >
//                       <td className="py-2 pr-2">
//                         <div className="font-semibold">
//                           {site.structure_type || "-"}
//                         </div>
//                         <div className="text-[10px] text-slate-400 break-all">
//                           {site.id}
//                         </div>
//                       </td>
//                       <td className="py-2 pr-2">{site.lat}</td>
//                       <td className="py-2 pr-2">{site.lon}</td>
//                       <td className="py-2 pr-2">
//                         <div className="flex gap-2">
//                           <button
//                             type="button"
//                             className={`px-2 py-1 rounded-full text-xs ${
//                               dec.status === "pass"
//                                 ? "bg-green-500 text-black"
//                                 : "bg-slate-800"
//                             }`}
//                             onClick={() =>
//                               updateDecision(site, "status", "pass")
//                             }
//                           >
//                             Pass
//                           </button>
//                           <button
//                             type="button"
//                             className={`px-2 py-1 rounded-full text-xs ${
//                               dec.status === "flag"
//                                 ? "bg-red-500 text-black"
//                                 : "bg-slate-800"
//                             }`}
//                             onClick={() =>
//                               updateDecision(site, "status", "flag")
//                             }
//                           >
//                             Flag
//                           </button>
//                         </div>
//                       </td>
//                       <td className="py-2 pr-2">
//                         {dec.status === "flag" && (
//                           <select
//                             className="bg-slate-800 px-2 py-1 rounded w-40"
//                             value={dec.reason || ""}
//                             onChange={(e) =>
//                               updateDecision(site, "reason", e.target.value)
//                             }
//                           >
//                             <option value="">Select reason</option>
//                             <option value="mis_marking">
//                               Mis-marking (structure at distance)
//                             </option>
//                             <option value="built_up">Built-up area</option>
//                             <option value="inside_water">
//                               Inside waterbody
//                             </option>
//                             <option value="no_structure">
//                               No visible structure
//                             </option>
//                             <option value="other">Other</option>
//                           </select>
//                         )}
//                       </td>
//                       <td className="py-2 pr-2">
//                         {dec.status === "flag" && (
//                           <input
//                             className="bg-slate-800 px-2 py-1 rounded w-40"
//                             placeholder="Optional notes"
//                             value={dec.comments || ""}
//                             onChange={(e) =>
//                               updateDecision(site, "comments", e.target.value)
//                             }
//                           />
//                         )}
//                       </td>

//                       {/* LULC manual */}
//                       <td className="py-2 pr-2">
//                         {isPass && (
//                           <input
//                             className="bg-slate-800 px-2 py-1 rounded w-32"
//                             placeholder="Croplands"
//                             value={dec.lulc_class || ""}
//                             onChange={(e) =>
//                               updateDecision(site, "lulc_class", e.target.value)
//                             }
//                           />
//                         )}
//                       </td>

//                       {/* Drainage distance manual */}
//                       <td className="py-2 pr-2">
//                         {isPass && (
//                           <input
//                             type="number"
//                             className="bg-slate-800 px-2 py-1 rounded w-24"
//                             placeholder="80"
//                             value={
//                               dec.drainage_distance !== undefined
//                                 ? dec.drainage_distance
//                                 : ""
//                             }
//                             onChange={(e) =>
//                               updateDecision(
//                                 site,
//                                 "drainage_distance",
//                                 e.target.value
//                               )
//                             }
//                           />
//                         )}
//                       </td>

//                       {/* Validate button */}
//                       <td className="py-2 pr-2">
//                         <button
//                           type="button"
//                           disabled={!isPass || validatingSiteId === site.id}
//                           onClick={() => handleValidateSite(site)}
//                           className={`px-3 py-1 rounded-full text-xs border ${
//                             !isPass || validatingSiteId === site.id
//                               ? "border-slate-600 text-slate-500"
//                               : "border-indigo-400 text-indigo-200 hover:bg-indigo-500/10"
//                           }`}
//                         >
//                           {validatingSiteId === site.id
//                             ? "Validating..."
//                             : "Validate"}
//                         </button>
//                       </td>
//                     </tr>
//                   );
//                 })}
//               </tbody>
//             </table>

//             {/* Decision summary and submit */}
//             <div className="mt-4 flex flex-col gap-2 text-xs text-slate-300">
//               <div>
//                 Decided: {decided}/{totalSites} | Flagged: {flaggedLocal}
//               </div>
//               <button
//                 type="button"
//                 onClick={handleSubmitReview}
//                 className="mt-1 bg-blue-500 text-black px-4 py-2 rounded-full font-semibold max-w-xs"
//               >
//                 {submitting ? "Submitting..." : "Submit Error 1 Review"}
//               </button>
//               {submitResult && (
//                 <div className="mt-2 text-green-400">
//                   Saved flagged sites: {submitResult.flagged_count} | Passed
//                   sites: {submitResult.passed_count}
//                 </div>
//               )}
//             </div>
//           </div>

//           {/* Map + Validation panel */}
//           <div className="flex flex-col gap-4">
//             <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl">
//               <h2 className="text-xl font-semibold mb-4">Satellite View</h2>
//               <SiteMap sites={sites} />
//             </div>

//             <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl text-xs">
//               <h2 className="text-sm font-semibold mb-2">
//                 Rule-based Validation Report
//               </h2>

//               {!validationResult && !validationError && (
//                 <p className="text-slate-300">
//                   Select a site marked{" "}
//                   <span className="text-green-400 font-semibold">Pass</span> and
//                   click <span className="font-semibold">Validate</span> to see
//                   GEE + rules.json evaluation here.
//                 </p>
//               )}

//               {validationError && (
//                 <div className="mt-2 rounded border border-rose-500/60 bg-rose-900/20 px-3 py-2 text-rose-200">
//                   {validationError}
//                 </div>
//               )}

//               {validationResult && (
//                 <ValidationDetail
//                   result={validationResult.data}
//                   siteLabel={validationResult.siteLabel}
//                   badgeColor={badgeColor}
//                 />
//               )}
//             </div>
//           </div>
//         </div>
//       )}
//     </div>
//   );
// }

// /* ---------- Validation detail components ---------- */

// function ValidationDetail({ result, siteLabel, badgeColor }) {
//   const params = result.evaluation?.parameters;
//   const raw = result.raw_values || {};

//   return (
//     <div className="mt-2 space-y-3">
//       <p className="text-[11px] text-slate-300">
//         Site: <span className="font-semibold">{siteLabel}</span>
//       </p>

//       <div>
//         <h3 className="font-semibold text-slate-100 mb-1 text-xs">
//           Raw values (from GEE + inputs)
//         </h3>
//         <div className="grid gap-1 md:grid-cols-2 text-[11px]">
//           <p>
//             <span className="font-medium text-slate-200">
//               Slope mean (30m):
//             </span>{" "}
//             {raw.slope_mean_30m} %
//           </p>
//           <p>
//             <span className="font-medium text-slate-200">
//               Catchment min (30m):
//             </span>{" "}
//             {raw.catchment_min_30m} ha
//           </p>
//           <p>
//             <span className="font-medium text-slate-200">
//               Catchment max (30m):
//             </span>{" "}
//             {raw.catchment_max_30m} ha
//           </p>
//           <p>
//             <span className="font-medium text-slate-200">Stream order:</span>{" "}
//             {raw.stream_order}
//           </p>
//           <p>
//             <span className="font-medium text-slate-200">
//               Drainage distance:
//             </span>{" "}
//             {raw.drainage_distance ?? "—"} m
//           </p>
//           <p>
//             <span className="font-medium text-slate-200">LULC:</span>{" "}
//             {raw.lulc_class || "—"}
//           </p>
//         </div>
//       </div>

//       <div className="space-y-2">
//         <ParamBlock
//           title="Slope"
//           param={params?.slope}
//           badgeColor={badgeColor}
//         />
//         <ParamBlock
//           title="Catchment Area"
//           param={params?.catchment_area}
//           badgeColor={badgeColor}
//         />
//         <ParamBlock
//           title="Stream Order"
//           param={params?.stream_order}
//           badgeColor={badgeColor}
//         />
//         <ParamBlock
//           title="Drainage Distance"
//           param={params?.drainage_distance}
//           badgeColor={badgeColor}
//         />
//         <ParamBlock title="LULC" param={params?.lulc} badgeColor={badgeColor} />
//       </div>

//       <p className="text-[11px] text-slate-400">
//         {result.evaluation?.overall_comment}
//       </p>
//     </div>
//   );
// }

// function ParamBlock({ title, param, badgeColor }) {
//   if (!param) return null;
//   return (
//     <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-2">
//       <div className="flex items-center justify-between mb-1">
//         <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-300">
//           {title}
//         </span>
//         <span
//           className={
//             "px-2 py-0.5 rounded-full border text-[11px] font-medium " +
//             badgeColor(param.category)
//           }
//         >
//           {param.category}
//         </span>
//       </div>
//       <p className="text-[11px] text-slate-200">{param.explanation}</p>
//     </div>
//   );
// }

// export default App;



///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


// experimental with lulc integration

import { useState, useEffect, useMemo } from "react";
import SiteMap from "./components/SiteMap";

const API_BASE = "http://localhost:8000";

const PROPOSED_BLOCKS_API =
  "https://geoserver.core-stack.org/api/v1/proposed_blocks/";

function PlanSelector({ onSelectionChange }) {
  const [states, setStates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const [selectedStateId, setSelectedStateId] = useState("");
  const [selectedDistrictId, setSelectedDistrictId] = useState("");
  const [selectedBlockId, setSelectedBlockId] = useState("");

  // Fetch once
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setErr("");
      try {
        const res = await fetch(PROPOSED_BLOCKS_API);
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        const data = await res.json();
        // data is: [ { label, state_id, district: [ ... ] }, ... ]
        setStates(Array.isArray(data) ? data : []);
      } catch (e) {
        console.error(e);
        setErr("Failed to load state/district/block list.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Find selected objects
  const selectedState = useMemo(
    () => states.find((s) => s.state_id === selectedStateId) || null,
    [states, selectedStateId]
  );

  const districtOptions = useMemo(
    () => (selectedState ? selectedState.district || [] : []),
    [selectedState]
  );

  const selectedDistrict = useMemo(
    () =>
      districtOptions.find((d) => d.district_id === selectedDistrictId) || null,
    [districtOptions, selectedDistrictId]
  );

  const blockOptions = useMemo(
    () => (selectedDistrict ? selectedDistrict.blocks || [] : []),
    [selectedDistrict]
  );

  const selectedBlock = useMemo(
    () => blockOptions.find((b) => b.block_id === selectedBlockId) || null,
    [blockOptions, selectedBlockId]
  );

  // Push selection to parent whenever it changes
  useEffect(() => {
    if (!onSelectionChange) return;
    onSelectionChange({
      stateLabel: selectedState?.label || "",
      stateId: selectedState?.state_id || "",
      districtLabel: selectedDistrict?.label || "",
      districtId: selectedDistrict?.district_id || "",
      blockLabel: selectedBlock?.label || "",
      blockId: selectedBlock?.block_id || "",
    });
  }, [selectedState, selectedDistrict, selectedBlock, onSelectionChange]);

  // Handlers
  const handleStateChange = (e) => {
    const v = e.target.value;
    setSelectedStateId(v);
    setSelectedDistrictId("");
    setSelectedBlockId("");
  };

  const handleDistrictChange = (e) => {
    const v = e.target.value;
    setSelectedDistrictId(v);
    setSelectedBlockId("");
  };

  const handleBlockChange = (e) => {
    const v = e.target.value;
    setSelectedBlockId(v);
  };

  return (
    <div className="space-y-2">
      {loading && (
        <p className="text-xs text-slate-400">Loading locations...</p>
      )}
      {err && <p className="text-xs text-red-400">{err}</p>}

      {/* State */}
      <div>
        <label className="block text-sm mb-1">State</label>
        <select
          className="w-full p-2 rounded bg-slate-800"
          value={selectedStateId}
          onChange={handleStateChange}
        >
          <option value="">Select state</option>
          {states.map((s) => (
            <option key={s.state_id} value={s.state_id}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      {/* District */}
      <div>
        <label className="block text-sm mb-1">District</label>
        <select
          className="w-full p-2 rounded bg-slate-800"
          value={selectedDistrictId}
          onChange={handleDistrictChange}
          disabled={!selectedStateId}
        >
          <option value="">Select district</option>
          {districtOptions.map((d) => (
            <option key={d.district_id} value={d.district_id}>
              {d.label}
            </option>
          ))}
        </select>
      </div>

      {/* Block */}
      <div>
        <label className="block text-sm mb-1">Block</label>
        <select
          className="w-full p-2 rounded bg-slate-800"
          value={selectedBlockId}
          onChange={handleBlockChange}
          disabled={!selectedDistrictId}
        >
          <option value="">Select block</option>
          {blockOptions.map((b) => (
            <option key={b.block_id} value={b.block_id}>
              {b.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}


function App() {
  const [planNumber, setPlanNumber] = useState("");
  const [district, setDistrict] = useState("");
  const [block, setBlock] = useState("");
  const [layerType, setLayerType] = useState("plan_agri");

  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [responseMeta, setResponseMeta] = useState(null);

  const [decisions, setDecisions] = useState({});
  const [submitResult, setSubmitResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // NEW: validation states
  const [validatingSiteId, setValidatingSiteId] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [validationError, setValidationError] = useState("");

  const handleFetchSites = async (e) => {
    e.preventDefault();

    if (!planNumber || !district || !block) {
      setError("Please fill all fields");
      return;
    }

    setError("");
    setLoading(true);
    setSites([]);
    setResponseMeta(null);
    setDecisions({});
    setSubmitResult(null);
    setValidationResult(null);
    setValidationError("");

    try {
      const res = await fetch(`${API_BASE}/api/plan-sites`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan_number: planNumber,
          district,
          block,
          layer_type: layerType,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "Something went wrong");
      } else {
        setSites(data.sites || []);
        setResponseMeta({
          plan_number: data.plan_number,
          district: data.district,
          block: data.block,
          layer_type: data.layer_type,
          layer_name: data.layer_name,
          site_count: data.site_count,
        });
      }
    } catch (err) {
      console.error(err);
      setError("Backend not reachable");
    } finally {
      setLoading(false);
    }
  };

  // update decision for a given site (extended with lulc_class + drainage_distance)
  const updateDecision = (site, field, value) => {
    setDecisions((prev) => {
      const prevSite = prev[site.id] || {};
      const base = {
        id: site.id,
        lat: site.lat,
        lon: site.lon,
        structure_type: site.structure_type,
        status: prevSite.status || "",
        reason: prevSite.reason || "",
        comments: prevSite.comments || "",
        lulc_class: prevSite.lulc_class || "",
        drainage_distance: prevSite.drainage_distance ?? "",
      };

      if (field === "status") {
        base.status = value;
        if (value === "pass") {
          // when passing, we only clear error-1 fields
          base.reason = "";
          base.comments = "";
        }
      } else if (field === "reason") {
        base.reason = value;
      } else if (field === "comments") {
        base.comments = value;
      } else if (field === "lulc_class") {
        base.lulc_class = value;
      } else if (field === "drainage_distance") {
        base.drainage_distance = value;
      }

      return {
        ...prev,
        [site.id]: base,
      };
    });
  };

  const handleSubmitReview = async () => {
    if (!responseMeta) {
      setError("Fetch sites first before submitting review.");
      return;
    }

    const allDecisions = Object.values(decisions);
    if (allDecisions.length === 0) {
      setError("You have not marked any site as Pass or Flag.");
      return;
    }

    setError("");
    setSubmitting(true);
    setSubmitResult(null);

    try {
      const res = await fetch(`${API_BASE}/api/error1/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan_number: responseMeta.plan_number,
          district: responseMeta.district,
          block: responseMeta.block,
          layer_type: responseMeta.layer_type,
          decisions: allDecisions,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "Failed to submit Error 1 review");
      } else {
        setSubmitResult(data);
      }
    } catch (err) {
      console.error(err);
      setError("Backend not reachable during submit");
    } finally {
      setSubmitting(false);
    }
  };

  // ---------- VALIDATION (Error 3-ish) ----------

  const handleValidateSite = async (site) => {
    setValidationError("");
    setValidationResult(null);
    setValidatingSiteId(site.id);

    const dec = decisions[site.id] || {};
    // For now manual entry; later we hook LULC + drainage from rasters
    const lulc = dec.lulc_class || null;
    const drainage =
      dec.drainage_distance !== "" && dec.drainage_distance !== undefined
        ? Number(dec.drainage_distance)
        : 80;

    try {
      const payload = {
        lat: site.lat,
        lon: site.lon,
        structure_type: site.structure_type || "Check dam",
        // lulc_class: lulc,
        // drainage_distance: drainage,
      };
      if (dec.lulc_class) {
        payload.lulc_class = dec.lulc_class;
      }

      if (dec.drainage_distance !== "" && dec.drainage_distance !== undefined) {
        payload.drainage_distance = Number(dec.drainage_distance);
      }

      const res = await fetch(`${API_BASE}/api/validate-site`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Validation failed");
      }

      setValidationResult({
        siteId: site.id,
        siteLabel: `${site.structure_type || ""} @ (${site.lat.toFixed(
          5
        )}, ${site.lon.toFixed(5)})`,
        data,
      });
    } catch (err) {
      console.error(err);
      setValidationError(err.message || "Failed to validate site");
    } finally {
      setValidatingSiteId(null);
    }
  };

  const totalSites = sites.length;
  const decided = Object.values(decisions).filter(
    (d) => d.status === "pass" || d.status === "flag"
  ).length;
  const flaggedLocal = Object.values(decisions).filter(
    (d) => d.status === "flag"
  ).length;

  // badge color helper for validation report
  const badgeColor = (category) => {
    switch (category) {
      case "accepted":
      case "valid":
        return "bg-emerald-500/20 text-emerald-200 border-emerald-400";
      case "partially_accepted":
      case "be_careful":
        return "bg-amber-500/20 text-amber-200 border-amber-400";
      case "not_accepted":
        return "bg-rose-500/20 text-rose-200 border-rose-400";
      case "not_evaluated":
      default:
        return "bg-slate-700 text-slate-200 border-slate-500";
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <h1 className="text-3xl font-bold mb-6">
        Plan Site Extraction & Error 1 Review
      </h1>

      {/* Input Form */}
      <div className="bg-slate-900 border border-slate-700 p-6 rounded-xl max-w-xl mb-8">
        <form onSubmit={handleFetchSites}>
          {/* NEW: cascading State → District → Block */}
          <PlanSelector
           onSelectionChange={({ districtLabel, blockLabel }) => {
              setDistrict(districtLabel ? districtLabel.toLowerCase() : "");
              setBlock(blockLabel ? blockLabel.toLowerCase() : "");
            }}

          />

          {/* Plan number still manual for now */}
          <label className="block text-sm mb-1 mt-4">Plan Number</label>
          <input
            className="w-full p-2 rounded bg-slate-800 mb-3"
            placeholder="116"
            value={planNumber}
            onChange={(e) => setPlanNumber(e.target.value)}
          />

          <label className="block text-sm mb-1">Layer Type</label>
          <select
            className="w-full p-2 rounded bg-slate-800 mb-4"
            value={layerType}
            onChange={(e) => setLayerType(e.target.value)}
          >
            <option value="plan_agri">Agriculture (plan_agri)</option>
            <option value="plan_gw">Groundwater (plan_gw)</option>
            <option value="waterbody">Waterbody (resources)</option>
          </select>

          {error && <p className="text-red-400 mb-3">{error}</p>}

          <button
            type="submit"
            className="bg-green-500 text-black px-4 py-2 rounded-full font-semibold"
          >
            {loading ? "Fetching..." : "Extract Sites"}
          </button>

          <p className="mt-2 text-[11px] text-slate-400">
            Selected district/block: {district || "—"} / {block || "—"}
          </p>
        </form>
      </div>

      {/* Response Summary */}
      {responseMeta && (
        <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl max-w-2xl mb-6 text-sm">
          <p>
            <b>Layer:</b> {responseMeta.layer_name}
          </p>
          <p>
            <b>Total Sites:</b> {responseMeta.site_count}
          </p>
          <p>
            <b>Location:</b> {responseMeta.district} / {responseMeta.block}
          </p>
          <p className="mt-2 text-slate-300 text-xs">
            Please use the satellite view on the right to visually check each
            point before marking Pass or Flag. Validation uses GEE for slope,
            catchment and stream order for sites marked <b>Pass</b>.
          </p>
        </div>
      )}

      {/* Table + Map + Validation */}
      {sites.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-6xl">
          {/* Table with decisions & validate */}
          <div className="bg-slate-900 border border-slate-700 p-6 rounded-xl overflow-x-auto">
            <h2 className="text-xl font-semibold mb-2">Extracted Sites</h2>
            <p className="text-xs text-slate-300 mb-4">
              1) Use map to review coordinates. 2) Mark{" "}
              <span className="text-green-400">Pass</span> /
              <span className="text-red-400">Flag</span>. 3) For passed sites,
              enter LULC & drainage (temporary manual) and click{" "}
              <span className="font-semibold">Validate</span>.
            </p>

            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="py-2 text-left">Structure</th>
                  <th className="py-2 text-left">Lat</th>
                  <th className="py-2 text-left">Lon</th>
                  <th className="py-2 text-left">Decision</th>
                  <th className="py-2 text-left">Reason (if Flag)</th>
                  <th className="py-2 text-left">Comments</th>
                  <th className="py-2 text-left">LULC</th>
                  <th className="py-2 text-left">Drain (m)</th>
                  <th className="py-2 text-left">Validate</th>
                </tr>
              </thead>
              <tbody>
                {sites.map((site) => {
                  const dec = decisions[site.id] || {};
                  const isPass = dec.status === "pass";

                  return (
                    <tr
                      key={site.id}
                      className="border-b border-slate-800 align-top"
                    >
                      <td className="py-2 pr-2">
                        <div className="font-semibold">
                          {site.structure_type || "-"}
                        </div>
                        <div className="text-[10px] text-slate-400 break-all">
                          {site.id}
                        </div>
                      </td>
                      <td className="py-2 pr-2">{site.lat}</td>
                      <td className="py-2 pr-2">{site.lon}</td>
                      <td className="py-2 pr-2">
                        <div className="flex gap-2">
                          <button
                            type="button"
                            className={`px-2 py-1 rounded-full text-xs ${
                              dec.status === "pass"
                                ? "bg-green-500 text-black"
                                : "bg-slate-800"
                            }`}
                            onClick={() =>
                              updateDecision(site, "status", "pass")
                            }
                          >
                            Pass
                          </button>
                          <button
                            type="button"
                            className={`px-2 py-1 rounded-full text-xs ${
                              dec.status === "flag"
                                ? "bg-red-500 text-black"
                                : "bg-slate-800"
                            }`}
                            onClick={() =>
                              updateDecision(site, "status", "flag")
                            }
                          >
                            Flag
                          </button>
                        </div>
                      </td>
                      <td className="py-2 pr-2">
                        {dec.status === "flag" && (
                          <select
                            className="bg-slate-800 px-2 py-1 rounded w-40"
                            value={dec.reason || ""}
                            onChange={(e) =>
                              updateDecision(site, "reason", e.target.value)
                            }
                          >
                            <option value="">Select reason</option>
                            <option value="mis_marking">
                              Mis-marking (structure at distance)
                            </option>
                            <option value="built_up">Built-up area</option>
                            <option value="inside_water">
                              Inside waterbody
                            </option>
                            <option value="no_structure">
                              No visible structure
                            </option>
                            <option value="other">Other</option>
                          </select>
                        )}
                      </td>
                      <td className="py-2 pr-2">
                        {dec.status === "flag" && (
                          <input
                            className="bg-slate-800 px-2 py-1 rounded w-40"
                            placeholder="Optional notes"
                            value={dec.comments || ""}
                            onChange={(e) =>
                              updateDecision(site, "comments", e.target.value)
                            }
                          />
                        )}
                      </td>

                      {/* LULC manual */}
                      <td className="py-2 pr-2">
                        {isPass && (
                          <input
                            className="bg-slate-800 px-2 py-1 rounded w-32"
                            placeholder="Croplands"
                            value={dec.lulc_class || ""}
                            onChange={(e) =>
                              updateDecision(site, "lulc_class", e.target.value)
                            }
                          />
                        )}
                      </td>

                      {/* Drainage distance manual */}
                      <td className="py-2 pr-2">
                        {isPass && (
                          <input
                            type="number"
                            className="bg-slate-800 px-2 py-1 rounded w-24"
                            placeholder="80"
                            value={
                              dec.drainage_distance !== undefined
                                ? dec.drainage_distance
                                : ""
                            }
                            onChange={(e) =>
                              updateDecision(
                                site,
                                "drainage_distance",
                                e.target.value
                              )
                            }
                          />
                        )}
                      </td>

                      {/* Validate button */}
                      <td className="py-2 pr-2">
                        <button
                          type="button"
                          disabled={!isPass || validatingSiteId === site.id}
                          onClick={() => handleValidateSite(site)}
                          className={`px-3 py-1 rounded-full text-xs border ${
                            !isPass || validatingSiteId === site.id
                              ? "border-slate-600 text-slate-500"
                              : "border-indigo-400 text-indigo-200 hover:bg-indigo-500/10"
                          }`}
                        >
                          {validatingSiteId === site.id
                            ? "Validating..."
                            : "Validate"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* Decision summary and submit */}
            <div className="mt-4 flex flex-col gap-2 text-xs text-slate-300">
              <div>
                Decided: {decided}/{totalSites} | Flagged: {flaggedLocal}
              </div>
              <button
                type="button"
                onClick={handleSubmitReview}
                className="mt-1 bg-blue-500 text-black px-4 py-2 rounded-full font-semibold max-w-xs"
              >
                {submitting ? "Submitting..." : "Submit Error 1 Review"}
              </button>
              {submitResult && (
                <div className="mt-2 text-green-400">
                  Saved flagged sites: {submitResult.flagged_count} | Passed
                  sites: {submitResult.passed_count}
                </div>
              )}
            </div>
          </div>

          {/* Map + Validation panel */}
          <div className="flex flex-col gap-4">
            <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl">
              <h2 className="text-xl font-semibold mb-4">Satellite View</h2>
              <SiteMap sites={sites} />
            </div>

            <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl text-xs">
              <h2 className="text-sm font-semibold mb-2">
                Rule-based Validation Report
              </h2>

              {!validationResult && !validationError && (
                <p className="text-slate-300">
                  Select a site marked{" "}
                  <span className="text-green-400 font-semibold">Pass</span> and
                  click <span className="font-semibold">Validate</span> to see
                  GEE + rules.json evaluation here.
                </p>
              )}

              {validationError && (
                <div className="mt-2 rounded border border-rose-500/60 bg-rose-900/20 px-3 py-2 text-rose-200">
                  {validationError}
                </div>
              )}

              {validationResult && (
                <ValidationDetail
                  result={validationResult.data}
                  siteLabel={validationResult.siteLabel}
                  badgeColor={badgeColor}
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------- Validation detail components ---------- */

function ValidationDetail({ result, siteLabel, badgeColor }) {
  const params = result.evaluation?.parameters;
  const raw = result.raw_values || {};

  return (
    <div className="mt-2 space-y-3">
      <p className="text-[11px] text-slate-300">
        Site: <span className="font-semibold">{siteLabel}</span>
      </p>

      <div>
        <h3 className="font-semibold text-slate-100 mb-1 text-xs">
          Raw values (from GEE + inputs)
        </h3>
        <div className="grid gap-1 md:grid-cols-2 text-[11px]">
          <p>
            <span className="font-medium text-slate-200">
              Slope mean (30m):
            </span>{" "}
            {raw.slope_mean_30m} %
          </p>
          <p>
            <span className="font-medium text-slate-200">
              Catchment min (30m):
            </span>{" "}
            {raw.catchment_min_30m} ha
          </p>
          <p>
            <span className="font-medium text-slate-200">
              Catchment max (30m):
            </span>{" "}
            {raw.catchment_max_30m} ha
          </p>
          <p>
            <span className="font-medium text-slate-200">Stream order:</span>{" "}
            {raw.stream_order}
          </p>
          <p>
            <span className="font-medium text-slate-200">
              Drainage distance:
            </span>{" "}
            {raw.drainage_distance ?? "—"} m
          </p>
          <p>
            <span className="font-medium text-slate-200">LULC:</span>{" "}
            {raw.lulc_class || "—"}
          </p>
        </div>
      </div>

      <div className="space-y-2">
        <ParamBlock
          title="Slope"
          param={params?.slope}
          badgeColor={badgeColor}
        />
        <ParamBlock
          title="Catchment Area"
          param={params?.catchment_area}
          badgeColor={badgeColor}
        />
        <ParamBlock
          title="Stream Order"
          param={params?.stream_order}
          badgeColor={badgeColor}
        />
        <ParamBlock
          title="Drainage Distance"
          param={params?.drainage_distance}
          badgeColor={badgeColor}
        />
        <ParamBlock title="LULC" param={params?.lulc} badgeColor={badgeColor} />
      </div>

      <p className="text-[11px] text-slate-400">
        {result.evaluation?.overall_comment}
      </p>
    </div>
  );
}

function ParamBlock({ title, param, badgeColor }) {
  if (!param) return null;
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-2">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-300">
          {title}
        </span>
        <span
          className={
            "px-2 py-0.5 rounded-full border text-[11px] font-medium " +
            badgeColor(param.category)
          }
        >
          {param.category}
        </span>
      </div>
      <p className="text-[11px] text-slate-200">{param.explanation}</p>
    </div>
  );
}

export default App;

