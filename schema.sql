-- 多租户机构管理系统建表SQL

-- 机构表
CREATE TABLE IF NOT EXISTS t_organization (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '机构ID',
    org_name VARCHAR(100) NOT NULL COMMENT '机构名称',
    status TINYINT DEFAULT 1 COMMENT '状态: 1-正常, 0-禁用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='机构表';

-- 班级表
CREATE TABLE IF NOT EXISTS t_class (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '班级ID',
    org_id BIGINT NOT NULL COMMENT '机构ID',
    class_name VARCHAR(100) NOT NULL COMMENT '班级名称',
    teacher_name VARCHAR(50) DEFAULT '' COMMENT '班主任姓名',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_org_id (org_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='班级表';

-- 教师表
CREATE TABLE IF NOT EXISTS t_teacher (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '教师ID',
    openid VARCHAR(100) NOT NULL COMMENT '微信openid',
    org_id BIGINT NOT NULL COMMENT '机构ID',
    class_id BIGINT DEFAULT NULL COMMENT '班级ID',
    phone VARCHAR(20) DEFAULT '' COMMENT '手机号',
    role VARCHAR(20) DEFAULT 'teacher' COMMENT '角色: admin-管理员, teacher-教师',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE INDEX idx_openid (openid),
    INDEX idx_org_id (org_id),
    INDEX idx_class_id (class_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师表';
