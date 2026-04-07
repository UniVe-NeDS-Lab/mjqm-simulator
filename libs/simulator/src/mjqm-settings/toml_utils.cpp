//
// Created by Marco Ciotola on 05/02/25.
//

#define TOML_IMPLEMENTATION
#include <mjqm-settings/toml_utils.h>

void ensure_table_at_path(toml::table& data, const toml::path& path) {
    auto parent_node = data.at_path(path);
    if (!parent_node.is_table()) {
        data.at_path(path.parent()).as_table()->insert_or_assign(path.leaf().str(), toml::table{});
    }
};

template <typename VALUE_TYPE>
void overwrite_value(toml::table& data, const toml::path& path, const VALUE_TYPE& value) {
    ensure_table_at_path(data, path.parent());
    auto parent_table = data.at_path(path.parent()).as_table();
    parent_table->insert_or_assign(path.leaf().str(), value);
}
template void overwrite_value(toml::table&, const toml::path&, const double&);
template void overwrite_value(toml::table&, const toml::path&, const long&);
template void overwrite_value(toml::table&, const toml::path&, const bool&);
template void overwrite_value(toml::table&, const toml::path&, const toml::table&);

toml::node_type interpreted_node_type(const toml::node_view<toml::node>& node) {
    if (node.is_boolean()) {
        return toml::node_type::boolean;
    } else if (node.is_integer()) {
        return toml::node_type::integer;
    } else if (node.is_floating_point()) {
        return toml::node_type::floating_point;
    } else if (node.is_string()) {
        return toml::node_type::string;
    } else {
        return toml::node_type::none;
    }
}

toml::node_type interpreted_node_type(const toml::node_view<toml::node>& node, const std::string& value) {
    if (!node) {
        if (value == "true" || value == "false") {
            return toml::node_type::boolean;
        } else if (value.find_first_not_of("-+0123456789") == std::string::npos) {
            return toml::node_type::integer;
        } else if (value.find_first_not_of("-+0123456789.") == std::string::npos) {
            return toml::node_type::floating_point;
        }
        return toml::node_type::string;
    }
    return interpreted_node_type(node);
}

template <>
void overwrite_value<std::string>(toml::table& data, const toml::path& path, const std::string& value) {
    ensure_table_at_path(data, path.parent());
    auto parent_node = data.at_path(path.parent()).as_table();
    auto current_node = data.at_path(path);
    auto type = interpreted_node_type(current_node, value);
    if (type == toml::node_type::none || type == toml::node_type::string) {
        parent_node->insert_or_assign(path.leaf().str(), value);
    } else if (type == toml::node_type::boolean) {
        parent_node->insert_or_assign(path.leaf().str(), value == "true");
    } else if (type == toml::node_type::integer) {
        parent_node->insert_or_assign(path.leaf().str(), std::stol(value));
    } else if (type == toml::node_type::floating_point) {
        parent_node->insert_or_assign(path.leaf().str(), std::stod(value));
    }
}

template <typename VALUE_TYPE>
void overwrite_value(toml::table& data, const std::string_view& key, const VALUE_TYPE& value) {
    toml::path path(key);
    overwrite_value<VALUE_TYPE>(data, path, value);
}
template void overwrite_value(toml::table&, const std::string_view&, const std::string&);
template void overwrite_value(toml::table&, const std::string_view&, const double&);
template void overwrite_value(toml::table&, const std::string_view&, const long&);
template void overwrite_value(toml::table&, const std::string_view&, const bool&);
template void overwrite_value(toml::table&, const std::string_view&, const toml::table&);
template <>
void overwrite_value(toml::table& data, const std::string_view& key, const std::string_view& value) {
    overwrite_value(data, key, std::string(value));
}
