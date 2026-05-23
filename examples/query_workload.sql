-- IonSense-QKG query workload
-- These queries assume a table or view named IonSenseQKG loaded from
-- metadata/datasets_qkg_ranked.csv.
-- Example DuckDB setup:
-- CREATE OR REPLACE VIEW IonSenseQKG AS
-- SELECT * FROM read_csv_auto('metadata/datasets_qkg_ranked.csv', header=true);

-- Q1: NISQ-feasible hybrid QML datasets with clear labels.
SELECT
    dataset_name,
    modality,
    task_type,
    estimated_qubits_min,
    estimated_qubits_max,
    qrs
FROM IonSenseQKG
WHERE access_status = 'public'
  AND estimated_qubits_max <= 8
  AND label_type IS NOT NULL
ORDER BY qrs DESC, dataset_name ASC;

-- Q2: Quantum time-series candidates requiring representation learning.
SELECT
    dataset_name,
    task_type,
    modality,
    sequence_type,
    preprocessing_need,
    candidate_quantum_encoding
FROM IonSenseQKG
WHERE lower(sequence_type) LIKE '%time-series%'
  AND (
        lower(preprocessing_need) LIKE '%window%'
        OR lower(preprocessing_need) LIKE '%aggregation%'
        OR lower(preprocessing_need) LIKE '%feature extraction%'
      )
  AND access_status = 'public'
ORDER BY qrs DESC, dataset_name ASC;

-- Q3: Limited-label anomaly and failure detection candidates.
SELECT
    dataset_name,
    task_type,
    modality,
    label_type,
    scale_summary,
    qrs
FROM IonSenseQKG
WHERE (
        lower(task_type) LIKE '%fault%'
        OR lower(task_type) LIKE '%anomaly%'
        OR lower(task_type) LIKE '%failure%'
        OR lower(task_type) LIKE '%thermal%'
      )
  AND access_status = 'public'
ORDER BY qrs DESC, dataset_name ASC;

-- Q4: Promising modalities for quantum feature maps.
SELECT
    modality,
    COUNT(*) AS n_datasets,
    ROUND(AVG(qrs), 3) AS avg_qrs,
    MIN(estimated_qubits_min) AS min_qubits,
    MAX(estimated_qubits_max) AS max_qubits
FROM IonSenseQKG
GROUP BY modality
ORDER BY avg_qrs DESC, n_datasets DESC, modality ASC;

-- Q5: Benchmark-ready datasets with source papers or baselines.
SELECT
    dataset_name,
    task_type,
    modality,
    label_type,
    baseline_available,
    related_papers_count,
    qrs
FROM IonSenseQKG
WHERE label_type IS NOT NULL
  AND access_status = 'public'
  AND related_papers_count >= 1
  AND lower(preprocessing_need) NOT LIKE '%heavy reconstruction%'
ORDER BY qrs DESC, dataset_name ASC;

-- Q6: High-QRS compact diagnostic datasets.
SELECT
    dataset_name,
    modality,
    sequence_type,
    candidate_quantum_encoding,
    qrs
FROM IonSenseQKG
WHERE qrs >= 0.8
  AND (
        lower(modality) LIKE '%eis%'
        OR lower(modality) LIKE '%impedance%'
        OR lower(modality) LIKE '%relaxation%'
        OR lower(sequence_type) LIKE '%curve%'
        OR lower(sequence_type) LIKE '%spectral%'
      )
ORDER BY qrs DESC, dataset_name ASC;

-- Q7: Datasets not directly NISQ-ready but useful after classical embeddings.
SELECT
    dataset_name,
    modality,
    sequence_type,
    preprocessing_need,
    candidate_quantum_encoding,
    qrs
FROM IonSenseQKG
WHERE nisq_feasibility = 'low'
   OR lower(candidate_quantum_encoding) LIKE '%embedding%'
ORDER BY qrs ASC, dataset_name ASC;
