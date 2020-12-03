# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import re
import sys
from unittest.mock import patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tssc import StepResult, StepRunnerException
from tssc.step_implementers.static_code_analysis import SonarQube


class TestStepImplementerSonarQubePackageBase(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=SonarQube,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

# TESTS FOR configuration checks
    def test_step_implementer_config_defaults(self):
        defaults = SonarQube.step_implementer_config_defaults()
        expected_defaults = {
            'properties': './sonar-project.properties'
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = SonarQube._required_config_or_result_keys()
        expected_required_keys = [
            'url',
            'application-name',
            'service-name',
            'version'
        ]
        self.assertEqual(required_keys, expected_required_keys)

    def test__validate_required_config_or_previous_step_result_artifact_keys_valid(self):
        step_config = {
            'url' : 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
            'application-name': 'app-name',
            'service-name': 'service-name',
            'username': 'username',
            'password': 'password',
            'version': 'notused'
        }

        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_invalid_missing_password(self):
        step_config = {
            'url' : 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
            'application-name': 'app-name',
            'service-name': 'service-name',
            'username': 'username',
            'version': 'notused'
        }
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path
            )
            with self.assertRaisesRegex(
                StepRunnerException,
                r"Either 'username' or 'password 'is not set. Neither or both must be set."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test__validate_required_config_or_previous_step_result_artifact_keys_invalid_missing_username(self):
        step_config = {
            'url' : 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
            'application-name': 'app-name',
            'service-name': 'service-name',
            'password': 'password',
            'version': 'notused'
        }
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path
            )
            with self.assertRaisesRegex(
                StepRunnerException,
                r"Either 'username' or 'password 'is not set. Neither or both must be set."
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    @patch('sh.sonar_scanner', create=True)
    def test_run_step_pass(self, sonar_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('sonar-project.properties',b'''testing''')
            properties_path = os.path.join(temp_dir.path, 'sonar-project.properties')

            step_config = {
                'properties': properties_path,
                'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                'application-name': 'app-name',
                'service-name': 'service-name',
                'username': 'username',
                'password': 'password'

            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            artifact_config = {
                'version': {'description': '', 'value': '1.0-123abc'},
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='static-code-analysis',
                sub_step_name='SonarQube',
                sub_step_implementer_name='SonarQube'
            )
            expected_step_result.add_artifact(
                name='sonarqube-result-set',
                value=f'{temp_dir.path}/working/report-task.txt'
            )

            sonar_mock.assert_called_once_with(
                    '-Dproject.settings=' + properties_path,
                    '-Dsonar.host.url=https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                    '-Dsonar.projectVersion=1.0-123abc',
                    '-Dsonar.projectKey=app-name:service-name',
                    '-Dsonar.login=username',
                    '-Dsonar.password=password',
                    '-Dsonar.working.directory=' + work_dir_path,
                    _out=sys.stdout,
                    _err=sys.stderr
            )

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    @patch('sh.sonar_scanner', create=True)
    def test_run_step_pass_no_username_and_password(self, sonar_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('sonar-project.properties',b'''testing''')
            properties_path = os.path.join(temp_dir.path, 'sonar-project.properties')

            step_config = {
                'properties': properties_path,
                'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                'application-name': 'app-name',
                'service-name': 'service-name'

            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            artifact_config = {
                'version': {'description': '', 'value': '1.0-123abc'},
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='static-code-analysis',
                sub_step_name='SonarQube',
                sub_step_implementer_name='SonarQube'
            )
            expected_step_result.add_artifact(
                name='sonarqube-result-set',
                value=f'{temp_dir.path}/working/report-task.txt'
            )

            sonar_mock.assert_called_once_with(
                    '-Dproject.settings=' + properties_path,
                    '-Dsonar.host.url=https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                    '-Dsonar.projectVersion=1.0-123abc',
                    '-Dsonar.projectKey=app-name:service-name',
                    '-Dsonar.working.directory=' + work_dir_path,
                    _out=sys.stdout,
                    _err=sys.stderr
            )

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    @patch('sh.sonar_scanner', create=True)
    def test_run_step_fail_no_properties(self, sonar_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')

            step_config = {
                'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                'application-name': 'app-name',
                'service-name': 'service-name'

            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            artifact_config = {
                'version': {'description': '', 'value': '1.0-123abc'},
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='static-code-analysis',
                sub_step_name='SonarQube',
                sub_step_implementer_name='SonarQube'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Properties file not found: ./sonar-project.properties'

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    @patch('sh.sonar_scanner', create=True)
    def test_run_step_fail_sonar_error(self, sonar_mock):
        with TempDirectory() as temp_dir:
            results_dir_path = os.path.join(temp_dir.path, 'tssc-results')
            results_file_name = 'tssc-results.yml'
            work_dir_path = os.path.join(temp_dir.path, 'working')
            temp_dir.write('sonar-project.properties',b'''testing''')
            properties_path = os.path.join(temp_dir.path, 'sonar-project.properties')

            step_config = {
                'properties': properties_path,
                'url': 'https://sonarqube-sonarqube.apps.tssc.rht-set.com',
                'application-name': 'app-name',
                'service-name': 'service-name',
                'username': 'username',
                'password': 'password'

            }

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='static-code-analysis',
                implementer='SonarQube',
                results_dir_path=results_dir_path,
                results_file_name=results_file_name,
                work_dir_path=work_dir_path,
            )

            artifact_config = {
                'version': {'description': '', 'value': '1.0-123abc'},
            }

            self.setup_previous_result(work_dir_path, artifact_config)

            sonar_mock.side_effect = sh.ErrorReturnCode('sonar', b'mock out', b'mock error')

            with self.assertRaisesRegex(
                RuntimeError,
                "Error invoking sonarscanner:"
            ):
                step_implementer._run_step()