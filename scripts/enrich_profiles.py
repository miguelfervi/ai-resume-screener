#!/usr/bin/env python3
"""One-shot enricher: expand seed profiles with fuller CV content.

Usage (repo root):
    python scripts/enrich_profiles.py
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed" / "profiles.json"

ROLE_SKILLS: dict[str, list[str]] = {
    "backend": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker", "AWS", "pytest", "Kafka", "gRPC"],
    "data": ["Python", "Spark", "SQL", "Airflow", "dbt", "BigQuery", "Pandas", "TensorFlow", "Kafka", "Docker"],
    "frontend": ["React", "TypeScript", "CSS", "Vite", "Testing Library", "Next.js", "Storybook", "GraphQL", "Jest", "Accessibility"],
    "fullstack": ["JavaScript", "TypeScript", "Node.js", "React", "MongoDB", "GraphQL", "PostgreSQL", "Docker", "CI/CD", "AWS"],
    "devops": ["Kubernetes", "Terraform", "Go", "AWS", "Prometheus", "Grafana", "Helm", "Linux", "CI/CD", "Python"],
    "qa": ["Selenium", "Cypress", "Python", "Playwright", "Jira", "Postman", "pytest", "API Testing", "CI/CD", "SQL"],
    "ml": ["Python", "PyTorch", "MLflow", "scikit-learn", "Pandas", "Kubernetes", "SQL", "Hugging Face", "Docker", "Feature Stores"],
    "product": ["Product Strategy", "Agile", "Figma", "Analytics", "Roadmapping", "A/B Testing", "SQL", "Stakeholder Mgmt", "Jira", "OKRs"],
    "java": ["Java", "Spring Boot", "Kafka", "PostgreSQL", "Maven", "Hibernate", "Microservices", "Docker", "JUnit", "AWS"],
    "design": ["Figma", "Sketch", "Prototyping", "User Research", "Design Systems", "Accessibility", "FigJam", "Usability Testing", "HTML", "CSS"],
    "python": ["Python", "Django", "FastAPI", "Celery", "Redis", "Linux", "PostgreSQL", "pytest", "Docker", "Bash"],
    "security": ["Security", "OWASP", "Python", "Burp Suite", "SIEM", "Threat Modeling", "Secure SDLC", "Linux", "Cloud Security", "IAM"],
    "analyst": ["SQL", "Tableau", "Excel", "R", "Power BI", "Python", "Statistics", "ETL", "Looker", "Data Modeling"],
    "ios": ["Swift", "SwiftUI", "Xcode", "Core Data", "Combine", "UIKit", "TestFlight", "CI/CD", "REST", "GraphQL"],
    "sre": ["Kubernetes", "Python", "Grafana", "Linux", "CI/CD", "Prometheus", "On-call", "Terraform", "SLO/SLA", "Incident Response"],
    "writer": ["Technical Writing", "Markdown", "API Docs", "Git", "Confluence", "OpenAPI", "Docs-as-code", "Sphinx", "Docusaurus", "Editing"],
    "manager": ["Leadership", "Python", "System Design", "Hiring", "Agile", "Mentoring", "Roadmaps", "OKRs", "Stakeholder Mgmt", "Architecture"],
    "rust": ["Rust", "C++", "Linux", "Networking", "WASM", "Tokio", "Performance", "Systems Design", "Git", "CI/CD"],
    "ba": ["Business Analysis", "BPMN", "SQL", "Jira", "Stakeholder Management", "Requirements", "Workshops", "Confluence", "Agile", "UML"],
    "cloud": ["AWS", "Python", "CloudFormation", "Lambda", "VPC", "CDK", "IAM", "ECS", "S3", "Cost Optimization"],
    "game": ["Unity", "C#", "Game Design", "Blender", "Shader Graph", "Mobile", "Profiling", "Git", "CI/CD", "UI Toolkit"],
    "scrum": ["Scrum", "Kanban", "Facilitation", "Coaching", "Jira", "Retrospectives", "Metrics", "Conflict Resolution", "Agile", "SAFe"],
    "dba": ["PostgreSQL", "SQL", "Linux", "Backup", "Replication", "Performance Tuning", "HA", "Monitoring", "Python", "Shell"],
}

ROLE_BY_HEADLINE = [
    ("backend", ("backend", "software engineer", "ingeniera backend", "ingeniero de software", "ingeniera de software", "desarrolladora python", "desarrollador python", "python software")),
    ("data", ("data engineer", "ingeniero de datos")),
    ("frontend", ("frontend",)),
    ("fullstack", ("full stack", "full-stack")),
    ("devops", ("devops",)),
    ("qa", ("qa",)),
    ("ml", ("machine learning", "ml engineer", "ingeniera de machine")),
    ("product", ("product manager",)),
    ("java", ("java",)),
    ("design", ("ux", "ui designer")),
    ("python", ("python developer", "junior")),
    ("security", ("security",)),
    ("analyst", ("data analyst", "business analyst")),
    ("ios", ("ios",)),
    ("sre", ("sre", "platform")),
    ("writer", ("technical writer",)),
    ("manager", ("engineering manager",)),
    ("rust", ("rust", "systems")),
    ("ba", ("business analyst",)),
    ("cloud", ("cloud architect",)),
    ("game", ("game",)),
    ("scrum", ("scrum",)),
    ("dba", ("database", "dba")),
]


def role_of(headline: str) -> str:
    h = headline.lower()
    for role, keys in ROLE_BY_HEADLINE:
        if any(k in h for k in keys):
            return role
    return "backend"


def phone_for(slug: str, locale: str) -> str:
    n = int(hashlib.md5(slug.encode()).hexdigest()[:8], 16)
    if locale == "es":
        return f"+34 6{n % 100_000_000:08d}"
    return f"+1 (555) {n % 10000:04d}-{(n // 7) % 10000:04d}"


def linkedin_for(slug: str) -> str:
    return f"linkedin.com/in/{slug}"


def merge_skills(existing: list[str], role: str) -> list[str]:
    extras = ROLE_SKILLS.get(role, ROLE_SKILLS["backend"])
    out: list[str] = []
    for s in existing + extras:
        if s not in out:
            out.append(s)
    return out[:10]


def expand_summary(p: dict) -> str:
    locale = p.get("locale", "en")
    name = p["full_name"].split()[0]
    role = p.get("headline", "professional")
    skills = ", ".join(p.get("skills", [])[:4])
    loc = p.get("location", "")
    years = 3 + (int(hashlib.md5(p["slug"].encode()).hexdigest()[:2], 16) % 8)

    if locale == "es":
        return (
            f"{name} es {role.lower()} con {years} años de experiencia en entornos de producto y tecnología. "
            f"Ha trabajado en equipos multidisciplinares entregando soluciones con {skills}. "
            f"Busca roles con impacto técnico y colaboración cercana con negocio"
            + (f" desde {loc}." if loc else ".")
        )
    return (
        f"{name} is a {role} with {years} years of experience shipping production systems. "
        f"Strong hands-on background with {skills}, collaborating across product and engineering. "
        f"Interested in roles with technical ownership and measurable impact"
        + (f" in {loc}." if loc else ".")
    )


def expand_jobs(p: dict) -> list[dict]:
    locale = p.get("locale", "en")
    existing = deepcopy(p.get("experience") or [])
    loc = p.get("location", "")
    role = role_of(p.get("headline", ""))
    skills = p.get("skills", [])[:3]

    # Enrich existing jobs
    for job in existing:
        job.setdefault("location", loc)
        bullets = list(job.get("bullets") or [])
        while len(bullets) < 4:
            bullets.append(_extra_bullet(locale, role, skills, len(bullets)))
        job["bullets"] = bullets[:4]

    # Ensure at least 3 jobs
    prior_titles_en = {
        "backend": ("Software Engineer", "Junior Developer"),
        "data": ("Data Analyst", "BI Intern"),
        "frontend": ("UI Engineer", "Web Developer"),
        "fullstack": ("Backend Developer", "Junior Web Developer"),
        "devops": ("SysAdmin", "Junior DevOps"),
        "qa": ("QA Tester", "Support Engineer"),
        "ml": ("Data Scientist", "Research Intern"),
        "product": ("Associate Product Manager", "Business Analyst"),
        "java": ("Java Developer", "Software Engineer"),
        "design": ("Product Designer", "Junior Designer"),
        "python": ("Backend Developer", "Intern"),
        "security": ("IT Security Analyst", "SOC Analyst"),
        "analyst": ("Junior Analyst", "Reporting Specialist"),
        "ios": ("Mobile Developer", "Junior iOS Developer"),
        "sre": ("Platform Engineer", "SysAdmin"),
        "writer": ("Content Writer", "Documentation Intern"),
        "manager": ("Tech Lead", "Senior Engineer"),
        "rust": ("C++ Engineer", "Systems Intern"),
        "ba": ("Junior BA", "Process Analyst"),
        "cloud": ("Cloud Engineer", "Infrastructure Engineer"),
        "game": ("Gameplay Programmer", "Junior Developer"),
        "scrum": ("Agile Coach", "Project Coordinator"),
        "dba": ("SQL Developer", "Junior DBA"),
    }
    prior_titles_es = {
        "backend": ("Desarrollador/a de Software", "Desarrollador/a Junior"),
        "data": ("Analista de Datos", "Becario/a BI"),
        "frontend": ("Ingeniero/a UI", "Desarrollador/a Web"),
        "fullstack": ("Desarrollador/a Backend", "Desarrollador/a Web Junior"),
        "devops": ("Administrador/a de Sistemas", "DevOps Junior"),
        "qa": ("Tester QA", "Soporte Técnico"),
        "ml": ("Científico/a de Datos", "Becario/a investigación"),
        "product": ("Product Manager Asociado/a", "Analista de Negocio"),
        "java": ("Desarrollador/a Java", "Ingeniero/a de Software"),
        "design": ("Diseñador/a de Producto", "Diseñador/a Junior"),
        "python": ("Desarrollador/a Backend", "Becario/a"),
        "security": ("Analista de Seguridad", "Analista SOC"),
        "analyst": ("Analista Junior", "Especialista de Reporting"),
        "ios": ("Desarrollador/a Móvil", "iOS Junior"),
        "sre": ("Ingeniero/a de Plataforma", "SysAdmin"),
        "writer": ("Redactor/a", "Becario/a documentación"),
        "manager": ("Tech Lead", "Ingeniero/a Senior"),
        "rust": ("Ingeniero/a C++", "Becario/a sistemas"),
        "ba": ("BA Junior", "Analista de Procesos"),
        "cloud": ("Ingeniero/a Cloud", "Ingeniero/a Infra"),
        "game": ("Programador/a Gameplay", "Desarrollador/a Junior"),
        "scrum": ("Agile Coach", "Coordinador/a de Proyecto"),
        "dba": ("Desarrollador/a SQL", "DBA Junior"),
    }
    titles = (prior_titles_es if locale == "es" else prior_titles_en).get(role, prior_titles_en["backend"])
    companies = (
        ["NovaLabs", "BrightStack", "CoreSoft"]
        if locale == "en"
        else ["NovaLabs", "BrightStack", "CoreSoft"]
    )

    # Derive end year of oldest job to chain backwards
    def start_year(job: dict) -> int:
        try:
            return int(str(job.get("start", "2020"))[:4])
        except ValueError:
            return 2020

    cursor = min((start_year(j) for j in existing), default=2020)
    idx = 0
    while len(existing) < 3 and idx < len(titles):
        end = cursor - 1
        start = end - 2 - (idx % 2)
        existing.append(
            {
                "title": titles[idx],
                "company": companies[idx % len(companies)],
                "location": loc,
                "start": str(start),
                "end": str(end),
                "bullets": [
                    _extra_bullet(locale, role, skills, i) for i in range(4)
                ],
            }
        )
        cursor = start
        idx += 1

    return existing


def _extra_bullet(locale: str, role: str, skills: list[str], i: int) -> str:
    skill = skills[i % len(skills)] if skills else ("Python" if locale == "en" else "Python")
    if locale == "es":
        options = [
            f"Colaboró con producto para priorizar entregas usando {skill}",
            f"Mejoró la calidad del código con revisiones y pruebas automatizadas",
            f"Documentó procesos y decisiones técnicas para el equipo",
            f"Redujo tiempos de entrega mediante automatización con {skill}",
            f"Participó en guardias y resolución de incidencias en producción",
        ]
    else:
        options = [
            f"Partnered with product to ship incremental value using {skill}",
            f"Improved code quality through reviews and automated tests",
            f"Documented technical decisions and runbooks for the team",
            f"Cut delivery time by automating workflows with {skill}",
            f"Took part in on-call rotations and production incident response",
        ]
    return options[i % len(options)]


def make_projects(p: dict) -> list[dict]:
    locale = p.get("locale", "en")
    skill = (p.get("skills") or ["Python"])[0]
    if locale == "es":
        return [
            {
                "name": "Herramienta interna de reporting",
                "description": f"Dashboard y ETL ligero con {skill} para métricas de equipo.",
            },
            {
                "name": "Open source / side project",
                "description": f"Librería utilitaria publicada y mantenida en tiempo libre con foco en {skill}.",
            },
        ]
    return [
        {
            "name": "Internal reporting toolkit",
            "description": f"Lightweight ETL and dashboard built with {skill} for team metrics.",
        },
        {
            "name": "Open-source side project",
            "description": f"Maintained a small utility library focused on {skill} patterns.",
        },
    ]


def make_certs(p: dict) -> list[str]:
    locale = p.get("locale", "en")
    role = role_of(p.get("headline", ""))
    pool_en = {
        "cloud": ["AWS Solutions Architect Associate", "AWS Developer Associate"],
        "devops": ["CKA (Certified Kubernetes Administrator)", "HashiCorp Terraform Associate"],
        "security": ["CompTIA Security+", "OSCP (in progress)"],
        "scrum": ["PSM II", "PSPO I"],
        "ml": ["Deep Learning Specialization", "AWS ML Specialty"],
        "dba": ["PostgreSQL Professional", "AWS Database Specialty"],
    }
    pool_es = {
        "cloud": ["AWS Solutions Architect Associate", "AWS Developer Associate"],
        "devops": ["CKA (Certified Kubernetes Administrator)", "HashiCorp Terraform Associate"],
        "security": ["CompTIA Security+", "OSCP (en curso)"],
        "scrum": ["PSM II", "PSPO I"],
        "ml": ["Deep Learning Specialization", "AWS ML Specialty"],
        "dba": ["PostgreSQL Professional", "AWS Database Specialty"],
    }
    pool = pool_es if locale == "es" else pool_en
    return pool.get(role, ["Professional Scrum Master I"] if role == "scrum" else ["AWS Cloud Practitioner"])


def enrich(profile: dict) -> dict:
    p = deepcopy(profile)
    role = role_of(p.get("headline", ""))
    p["phone"] = phone_for(p["slug"], p.get("locale", "en"))
    p["linkedin"] = linkedin_for(p["slug"])
    p["skills"] = merge_skills(p.get("skills") or [], role)
    p["summary"] = expand_summary({**p, "skills": p["skills"]})
    p["experience"] = expand_jobs(p)
    p["projects"] = make_projects(p)
    p["certifications"] = make_certs(p)

    # Ensure education has at least one entry with details
    edu = deepcopy(p.get("education") or [])
    if edu and "details" not in edu[0]:
        if p.get("locale") == "es":
            edu[0]["details"] = "TFG / proyecto final con nota destacada; asignaturas de sistemas y datos."
        else:
            edu[0]["details"] = "Capstone project with distinction; coursework in systems and data."
    if len(edu) < 2:
        if p.get("locale") == "es":
            edu.append(
                {
                    "degree": "Curso de especialización",
                    "institution": "Plataforma online (Coursera / edX)",
                    "year": str(int(edu[0].get("year", "2020")) + 1) if edu else "2021",
                    "details": "Formación continua alineada con el stack actual.",
                }
            )
        else:
            edu.append(
                {
                    "degree": "Professional specialization course",
                    "institution": "Online platform (Coursera / edX)",
                    "year": str(int(edu[0].get("year", "2020")) + 1) if edu else "2021",
                    "details": "Continuing education aligned with current stack.",
                }
            )
    p["education"] = edu
    return p


def main() -> int:
    profiles = json.loads(SEED.read_text(encoding="utf-8"))
    enriched = [enrich(p) for p in profiles]
    SEED.write_text(
        json.dumps(enriched, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    sample = enriched[0]
    print(
        f"Enriched {len(enriched)} profiles → {SEED}\n"
        f"  sample {sample['slug']}: skills={len(sample['skills'])} "
        f"jobs={len(sample['experience'])} "
        f"bullets={sum(len(j['bullets']) for j in sample['experience'])} "
        f"summary_len={len(sample['summary'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
