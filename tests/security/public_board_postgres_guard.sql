-- Copyright (c) 2026 GoreeCloud
-- SPDX-License-Identifier: AGPL-3.0-only
--
-- Isolated PostgreSQL predicate/transaction regression for a public board.
-- Synthetic tables and records only, all within a rolled-back transaction.
-- This checks PostgreSQL semantics of the intended predicates, NOT the
-- actual Plane/Django ORM-generated SQL, middleware, or HTTP endpoint.
--
-- Run only via run_public_board_postgres_guard.sh with a disposable,
-- network-disabled PostgreSQL 17 container; never against production.

BEGIN;

CREATE TEMP TABLE gc_ws (
    id integer PRIMARY KEY,
    deleted_at timestamptz
);

CREATE TEMP TABLE gc_project (
    id integer PRIMARY KEY,
    workspace_id integer NOT NULL REFERENCES gc_ws (id),
    deleted_at timestamptz
);

CREATE TEMP TABLE gc_board (
    anchor text PRIMARY KEY,
    workspace_id integer NOT NULL REFERENCES gc_ws (id),
    project_id integer NOT NULL REFERENCES gc_project (id),
    entity_identifier integer,
    entity_name text NOT NULL,
    is_disabled boolean NOT NULL DEFAULT FALSE,
    deleted_at timestamptz
);

INSERT INTO gc_ws VALUES
    (1, NULL), (2, NULL), (3, now());

INSERT INTO gc_project VALUES
    (11, 1, NULL),
    (12, 1, now()),
    (21, 2, NULL),
    (31, 3, NULL);

INSERT INTO gc_board VALUES
    ('valid',             1, 11, 11, 'project', FALSE, NULL),
    ('disabled',          1, 11, 11, 'project', TRUE,  NULL),
    ('deleted_board',     1, 11, 11, 'project', FALSE, now()),
    ('wrong_entity',      1, 11, 11, 'module',  FALSE, NULL),
    ('wrong_identifier',  1, 11, 21, 'project', FALSE, NULL),
    ('deleted_project',   1, 12, 12, 'project', FALSE, NULL),
    ('deleted_workspace', 3, 31, 31, 'project', FALSE, NULL),
    ('cross_workspace',   2, 11, 11, 'project', FALSE, NULL);

-- Mirrors the intended fields of DeployBoardAnchorMixin's queryset.
-- All joins below are confined to these synthetic, temporary tables.
CREATE TEMP VIEW gc_public_board AS
SELECT b.anchor
FROM gc_board AS b
JOIN gc_project AS p ON p.id = b.project_id
JOIN gc_ws AS w ON w.id = b.workspace_id
WHERE b.entity_name = 'project'
  AND b.is_disabled = FALSE
  AND b.deleted_at IS NULL
  AND p.deleted_at IS NULL
  AND w.deleted_at IS NULL
  AND p.workspace_id = b.workspace_id
  AND b.entity_identifier = b.project_id;

DO $$
DECLARE
    count_visible integer;
BEGIN
    SELECT COUNT(*) INTO count_visible FROM gc_public_board;
    IF count_visible <> 1 THEN
        RAISE EXCEPTION 'Expected exactly one visible board, got %', count_visible;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM gc_public_board WHERE anchor = 'valid') THEN
        RAISE EXCEPTION 'Expected valid project board to be visible';
    END IF;
    RAISE NOTICE 'POSTGRES17_PUBLIC_BOARD_SCOPE_PASS: valid=1 denied=7';
END $$;

-- Revocation must affect the very next query, without a cached acceptance.
UPDATE gc_board SET is_disabled = TRUE WHERE anchor = 'valid';

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM gc_public_board) THEN
        RAISE EXCEPTION 'Revoked board was still visible after disabling';
    END IF;
    RAISE NOTICE 'POSTGRES17_PUBLIC_BOARD_REVOCATION_PASS: next_query_denied';
END $$;

ROLLBACK;
